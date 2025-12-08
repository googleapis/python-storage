# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
import asyncio
import google_crc32c
from google.api_core import exceptions
from google.api_core.retry_async import AsyncRetry

from typing import List, Optional, Tuple, Any, Dict

from google_crc32c import Checksum

from ._utils import raise_if_no_fast_crc32c
from google.cloud.storage._experimental.asyncio.async_read_object_stream import (
    _AsyncReadObjectStream,
)
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)
from google.cloud.storage._experimental.asyncio.retry.bidi_stream_retry_manager import (
    _BidiStreamRetryManager,
)
from google.cloud.storage._experimental.asyncio.retry.reads_resumption_strategy import (
    _ReadResumptionStrategy,
    _DownloadState,
)

from io import BytesIO
from google.cloud import _storage_v2
from google.cloud.storage._helpers import generate_random_56_bit_integer


_MAX_READ_RANGES_PER_BIDI_READ_REQUEST = 100


class AsyncMultiRangeDownloader:
    """Provides an interface for downloading multiple ranges of a GCS ``Object``
    concurrently.

    Example usage:

    .. code-block:: python

        client = AsyncGrpcClient().grpc_client
        mrd = await AsyncMultiRangeDownloader.create_mrd(
            client, bucket_name="chandrasiri-rs", object_name="test_open9"
        )
        my_buff1 = open('my_fav_file.txt', 'wb')
        my_buff2 = BytesIO()
        my_buff3 = BytesIO()
        my_buff4 = any_object_which_provides_BytesIO_like_interface()
        await mrd.download_ranges(
            [
                # (start_byte, bytes_to_read, writeable_buffer)
                (0, 100, my_buff1),
                (100, 20, my_buff2),
                (200, 123, my_buff3),
                (300, 789, my_buff4),
            ]
        )

        # verify data in buffers...
        assert my_buff2.getbuffer().nbytes == 20


    """

    @classmethod
    async def create_mrd(
        cls,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: str,
        object_name: str,
        generation_number: Optional[int] = None,
        read_handle: Optional[bytes] = None,
        retry_policy: Optional[AsyncRetry] = None,
    ) -> AsyncMultiRangeDownloader:
        """Initializes a MultiRangeDownloader and opens the underlying bidi-gRPC
        object for reading.

        :type client: :class:`~google.cloud.storage._experimental.asyncio.async_grpc_client.AsyncGrpcClient.grpc_client`
        :param client: The asynchronous client to use for making API requests.

        :type bucket_name: str
        :param bucket_name: The name of the bucket containing the object.

        :type object_name: str
        :param object_name: The name of the object to be read.

        :type generation_number: int
        :param generation_number: (Optional) If present, selects a specific
                                  revision of this object.

        :type read_handle: bytes
        :param read_handle: (Optional) An existing handle for reading the object.
                            If provided, opening the bidi-gRPC connection will be faster.

        :type retry_policy: :class:`~google.api_core.retry_async.AsyncRetry`
        :param retry_policy: (Optional) The retry policy to use for the ``open`` operation.

        :rtype: :class:`~google.cloud.storage._experimental.asyncio.async_multi_range_downloader.AsyncMultiRangeDownloader`
        :returns: An initialized AsyncMultiRangeDownloader instance for reading.
        """
        mrd = cls(client, bucket_name, object_name, generation_number, read_handle)
        await mrd.open(retry_policy=retry_policy)
        return mrd

    def __init__(
        self,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: str,
        object_name: str,
        generation_number: Optional[int] = None,
        read_handle: Optional[bytes] = None,
    ) -> None:
        """Constructor for AsyncMultiRangeDownloader, clients are not adviced to
         use it directly. Instead it's adviced to use the classmethod `create_mrd`.

        :type client: :class:`~google.cloud.storage._experimental.asyncio.async_grpc_client.AsyncGrpcClient.grpc_client`
        :param client: The asynchronous client to use for making API requests.

        :type bucket_name: str
        :param bucket_name: The name of the bucket containing the object.

        :type object_name: str
        :param object_name: The name of the object to be read.

        :type generation_number: int
        :param generation_number: (Optional) If present, selects a specific revision of
                                  this object.

        :type read_handle: bytes
        :param read_handle: (Optional) An existing read handle.
        """

        raise_if_no_fast_crc32c()

        self.client = client
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.generation_number = generation_number
        self.read_handle = read_handle
        self.read_obj_str: Optional[_AsyncReadObjectStream] = None
        self._is_stream_open: bool = False

        self._read_id_to_writable_buffer_dict = {}
        self._read_id_to_download_ranges_id = {}
        self._download_ranges_id_to_pending_read_ids = {}
        self.persisted_size: Optional[int] = None  # updated after opening the stream

    async def open(self, retry_policy: Optional[AsyncRetry] = None) -> None:
        """Opens the bidi-gRPC connection to read from the object.

        This method initializes and opens an `_AsyncReadObjectStream` (bidi-gRPC stream) to
        for downloading ranges of data from GCS ``Object``.

        "Opening" constitutes fetching object metadata such as generation number
        and read handle and sets them as attributes if not already set.
        """
        if self._is_stream_open:
            raise ValueError("Underlying bidi-gRPC stream is already open")

        if retry_policy is None:
            # Default policy: retry generic transient errors
            retry_policy = AsyncRetry(
                predicate=lambda e: isinstance(e, (exceptions.ServiceUnavailable, exceptions.DeadlineExceeded))
            )

        async def _do_open():
            self.read_obj_str = _AsyncReadObjectStream(
                client=self.client,
                bucket_name=self.bucket_name,
                object_name=self.object_name,
                generation_number=self.generation_number,
                read_handle=self.read_handle,
            )
            await self.read_obj_str.open()

            if self.read_obj_str.generation_number:
                self.generation_number = self.read_obj_str.generation_number
            if self.read_obj_str.read_handle:
                self.read_handle = self.read_obj_str.read_handle
            if self.read_obj_str.persisted_size is not None:
                self.persisted_size = self.read_obj_str.persisted_size

            self._is_stream_open = True

        # Execute open with retry policy
        await retry_policy(_do_open)()

    async def download_ranges(
        self,
        read_ranges: List[Tuple[int, int, BytesIO]],
        lock: asyncio.Lock = None,
        retry_policy: AsyncRetry = None
    ) -> None:
        """Downloads multiple byte ranges from the object into the buffers
        provided by user with automatic retries.

        :type read_ranges: List[Tuple[int, int, "BytesIO"]]
        :param read_ranges: A list of tuples, where each tuple represents a
            combintaion of byte_range and writeable buffer in format -
            (`start_byte`, `bytes_to_read`, `writeable_buffer`). Buffer has
            to be provided by the user, and user has to make sure appropriate
            memory is available in the application to avoid out-of-memory crash.

        :type lock: asyncio.Lock
        :param lock: (Optional) An asyncio lock to synchronize sends and recvs
            on the underlying bidi-GRPC stream. This is required when multiple
            coroutines are calling this method concurrently.

            i.e. Example usage with multiple coroutines:

            ```
            lock = asyncio.Lock()
            task1 = asyncio.create_task(mrd.download_ranges(ranges1, lock))
            task2 = asyncio.create_task(mrd.download_ranges(ranges2, lock))
            await asyncio.gather(task1, task2)

            ```

            If user want to call this method serially from multiple coroutines,
            then providing a lock is not necessary.

            ```
            await mrd.download_ranges(ranges1)
            await mrd.download_ranges(ranges2)

            # ... some other code code...

            ```

        :type retry_policy: :class:`~google.api_core.retry_async.AsyncRetry`
        :param retry_policy: (Optional) The retry policy to use for the operation.

        :raises ValueError: if the underlying bidi-GRPC stream is not open.
        :raises ValueError: if the length of read_ranges is more than 1000.
        :raises DataCorruption: if a checksum mismatch is detected while reading data.

        """

        if len(read_ranges) > 1000:
            raise ValueError(
                "Invalid input - length of read_ranges cannot be more than 1000"
            )

        if not self._is_stream_open:
            raise ValueError("Underlying bidi-gRPC stream is not open")

        if lock is None:
            lock = asyncio.Lock()

        if retry_policy is None:
            retry_policy = AsyncRetry(
                predicate=lambda e: isinstance(e, (exceptions.ServiceUnavailable, exceptions.DeadlineExceeded))
            )

        # Initialize Global State for Retry Strategy
        download_states = {}
        for read_range in read_ranges:
            read_id = generate_random_56_bit_integer()
            download_states[read_id] = _DownloadState(
                initial_offset=read_range[0],
                initial_length=read_range[1],
                user_buffer=read_range[2]
            )

        initial_state = {
            "download_states": download_states,
            "read_handle": self.read_handle,
            "routing_token": None
        }

        # Track attempts to manage stream reuse
        is_first_attempt = True

        def stream_opener(requests: List[_storage_v2.ReadRange], state: Dict[str, Any]):

            async def generator():
                nonlocal is_first_attempt

                async with lock:
                    current_handle = state.get("read_handle")
                    current_token = state.get("routing_token")

                    # We reopen if it's a redirect (token exists) OR if this is a retry
                    # (not first attempt). This prevents trying to send data on a dead
                    # stream from a previous failed attempt.
                    should_reopen = (not is_first_attempt) or (current_token is not None)

                    if should_reopen:
                        # Close existing stream if any
                        if self.read_obj_str:
                            await self.read_obj_str.close()

                        # Re-initialize stream
                        self.read_obj_str = _AsyncReadObjectStream(
                            client=self.client,
                            bucket_name=self.bucket_name,
                            object_name=self.object_name,
                            generation_number=self.generation_number,
                            read_handle=current_handle,
                        )

                        # Inject routing_token into metadata if present
                        metadata = []
                        if current_token:
                            metadata.append(("x-goog-request-params", f"routing_token={current_token}"))

                        await self.read_obj_str.open(metadata=metadata if metadata else None)
                        self._is_stream_open = True

                    # Mark first attempt as done; next time this runs it will be a retry
                    is_first_attempt = False

                    # Send Requests
                    for i in range(0, len(requests), _MAX_READ_RANGES_PER_BIDI_READ_REQUEST):
                        batch = requests[i : i + _MAX_READ_RANGES_PER_BIDI_READ_REQUEST]
                        await self.read_obj_str.send(
                            _storage_v2.BidiReadObjectRequest(read_ranges=batch)
                        )

                    while True:
                        response = await self.read_obj_str.recv()
                        if response is None:
                            break
                        yield response

            return generator()

        strategy = _ReadResumptionStrategy()
        retry_manager = _BidiStreamRetryManager(strategy, stream_opener)

        await retry_manager.execute(initial_state, retry_policy)

        if initial_state.get("read_handle"):
            self.read_handle = initial_state["read_handle"]

    async def close(self):
        """
        Closes the underlying bidi-gRPC connection.
        """
        if not self._is_stream_open:
            raise ValueError("Underlying bidi-gRPC stream is not open")

        if self.read_obj_str:
            await self.read_obj_str.close()
        self.read_obj_str = None
        self._is_stream_open = False

    @property
    def is_stream_open(self) -> bool:
        return self._is_stream_open
