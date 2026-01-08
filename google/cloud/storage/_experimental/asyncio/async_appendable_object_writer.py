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
"""
from __future__ import annotations

NOTE:
This is _experimental module for upcoming support for Rapid Storage.
(https://cloud.google.com/blog/products/storage-data-transfer/high-performance-storage-innovations-for-ai-hpc#:~:text=your%20AI%20workloads%3A-,Rapid%20Storage,-%3A%20A%20new)

APIs may not work as intended and are not stable yet. Feature is not
GA(Generally Available) yet, please contact your TAM (Technical Account Manager)
if you want to use these Rapid Storage APIs.

"""
from io import BufferedReader, BytesIO
import asyncio
import io
from typing import List, Optional, Tuple, Union

from google_crc32c import Checksum
from google.api_core import exceptions
from google.api_core.retry_async import AsyncRetry
from google.rpc import status_pb2
from google.cloud._storage_v2.types import BidiWriteObjectRedirectedError
from google.cloud._storage_v2.types.storage import BidiWriteObjectRequest


from . import _utils
from google.cloud import _storage_v2
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)
from google.cloud.storage._experimental.asyncio.async_write_object_stream import (
    _AsyncWriteObjectStream,
)
from google.cloud.storage._experimental.asyncio.retry.bidi_stream_retry_manager import (
    _BidiStreamRetryManager,
)
from google.cloud.storage._experimental.asyncio.retry.writes_resumption_strategy import (
    _WriteResumptionStrategy,
    _WriteState,
)


_MAX_CHUNK_SIZE_BYTES = 2 * 1024 * 1024  # 2 MiB
_DEFAULT_FLUSH_INTERVAL_BYTES = 16 * 1024 * 1024  # 16 MiB
_BIDI_WRITE_REDIRECTED_TYPE_URL = (
    "type.googleapis.com/google.storage.v2.BidiWriteObjectRedirectedError"
)


def _is_write_retryable(exc):
    """Predicate to determine if a write operation should be retried."""

    print("In _is_write_retryable method, exception:", exc)

    if isinstance(
        exc,
        (
            exceptions.InternalServerError,
            exceptions.ServiceUnavailable,
            exceptions.DeadlineExceeded,
            exceptions.TooManyRequests,
        ),
    ):
        return True

    grpc_error = None
    if isinstance(exc, exceptions.Aborted):
        grpc_error = exc.errors[0]
        trailers = grpc_error.trailing_metadata()
        if not trailers:
            return False

        status_details_bin = None
        for key, value in trailers:
            if key == "grpc-status-details-bin":
                status_details_bin = value
                break

        if status_details_bin:
            status_proto = status_pb2.Status()
            try:
                status_proto.ParseFromString(status_details_bin)
                for detail in status_proto.details:
                    if detail.type_url == _BIDI_WRITE_REDIRECTED_TYPE_URL:
                        return True
            except Exception:
                return False
    return False


class AsyncAppendableObjectWriter:
    """Class for appending data to a GCS Appendable Object asynchronously."""

    def __init__(
        self,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: str,
        object_name: str,
        generation: Optional[int] = None,
        write_handle: Optional[_storage_v2.BidiWriteHandle] = None,
        writer_options: Optional[dict] = None,
    ):
        """
        Class for appending data to a GCS Appendable Object.

        Example usage:

        ```

        from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
        from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import AsyncAppendableObjectWriter
        import asyncio

        client = AsyncGrpcClient().grpc_client
        bucket_name = "my-bucket"
        object_name = "my-appendable-object"

        # instantiate the writer
        writer = AsyncAppendableObjectWriter(client, bucket_name, object_name)
        # open the writer, (underlying gRPC bidi-stream will be opened)
        await writer.open()

        # append data, it can be called multiple times.
        await writer.append(b"hello world")
        await writer.append(b"some more data")

        # optionally flush data to persist.
        await writer.flush()

        # close the gRPC stream.
        # Please note closing the program will also close the stream,
        # however it's recommended to close the stream if no more data to append
        # to clean up gRPC connection (which means CPU/memory/network resources)
        await writer.close()
        ```

        :type client: :class:`~google.cloud.storage._experimental.asyncio.async_grpc_client.AsyncGrpcClient.grpc_client`
        :param client: async grpc client to use for making API requests.

        :type bucket_name: str
        :param bucket_name: The name of the GCS bucket containing the object.

        :type object_name: str
        :param object_name: The name of the GCS Appendable Object to be written.

        :type generation: Optional[int]
        :param generation: (Optional) If present, creates writer for that
            specific revision of that object. Use this to append data to an
            existing Appendable Object.

            Setting to ``0`` makes the `writer.open()` succeed only if
            object doesn't exist in the bucket (useful for not accidentally
            overwriting existing objects).

            Warning: If `None`, a new object is created. If an object with the
            same name already exists, it will be overwritten the moment
            `writer.open()` is called.

        :type write_handle: _storage_v2.BidiWriteHandle
        :param write_handle: (Optional) An handle for writing the object.
            If provided, opening the bidi-gRPC connection will be faster.

        :type writer_options: dict
        :param writer_options: (Optional) A dictionary of writer options.
            Supported options:
            - "FLUSH_INTERVAL_BYTES": int
                The number of bytes to append before "persisting" data in GCS
                servers. Default is `_DEFAULT_FLUSH_INTERVAL_BYTES`.
                Must be a multiple of `_MAX_CHUNK_SIZE_BYTES`.
        """
        _utils.raise_if_no_fast_crc32c()
        self.client = client
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.write_handle = write_handle
        self.generation = generation

        self.write_obj_stream: Optional[_AsyncWriteObjectStream] = None
        self._is_stream_open: bool = False
        # `offset` is the latest size of the object without staleless.
        self.offset: Optional[int] = None
        # `persisted_size` is the total_bytes persisted in the GCS server.
        # Please note: `offset` and `persisted_size` are same when the stream is
        # opened.
        self.persisted_size: Optional[int] = None
        if writer_options is None:
            writer_options = {}
        self.flush_interval = writer_options.get(
            "FLUSH_INTERVAL_BYTES", _DEFAULT_FLUSH_INTERVAL_BYTES
        )
        if self.flush_interval < _MAX_CHUNK_SIZE_BYTES:
            raise exceptions.OutOfRange(
                f"flush_interval must be >= {_MAX_CHUNK_SIZE_BYTES} , but provided {self.flush_interval}"
            )
        if self.flush_interval % _MAX_CHUNK_SIZE_BYTES != 0:
            raise exceptions.OutOfRange(
                f"flush_interval must be a multiple of {_MAX_CHUNK_SIZE_BYTES}, but provided {self.flush_interval}"
            )
        self.bytes_appended_since_last_flush = 0
        self._lock = asyncio.Lock()
        self._routing_token: Optional[str] = None
        self.object_resource: Optional[_storage_v2.Object] = None

    def _stream_opener(self, write_handle=None):
        """Helper to create a new _AsyncWriteObjectStream."""
        return _AsyncWriteObjectStream(
            client=self.client,
            bucket_name=self.bucket_name,
            object_name=self.object_name,
            generation_number=self.generation,
            write_handle=write_handle if write_handle else self.write_handle,
        )

    async def state_lookup(self) -> int:
        """Returns the persisted_size

        :rtype: int
        :returns: persisted size.

        :raises ValueError: If the stream is not open (i.e., `open()` has not
            been called).
        """
        if not self._is_stream_open:
            raise ValueError("Stream is not open. Call open() before state_lookup().")

        async with self._lock:
            await self.write_obj_stream.send(
                _storage_v2.BidiWriteObjectRequest(
                    state_lookup=True,
                )
            )
            response = await self.write_obj_stream.recv()
            self.persisted_size = response.persisted_size
            return self.persisted_size

    def _on_open_error(self, exc):
        """Extracts routing token and write handle on redirect error during open."""
        grpc_error = None
        if isinstance(exc, exceptions.Aborted) and exc.errors:
            grpc_error = exc.errors[0]

        if grpc_error:
            if isinstance(grpc_error, BidiWriteObjectRedirectedError):
                self._routing_token = grpc_error.routing_token
                if grpc_error.write_handle:
                    self.write_handle = grpc_error.write_handle
                return

            if hasattr(grpc_error, "trailing_metadata"):
                trailers = grpc_error.trailing_metadata()
                if not trailers:
                    return

                status_details_bin = None
                for key, value in trailers:
                    if key == "grpc-status-details-bin":
                        status_details_bin = value
                        break

                if status_details_bin:
                    status_proto = status_pb2.Status()
                    try:
                        status_proto.ParseFromString(status_details_bin)
                        for detail in status_proto.details:
                            if detail.type_url == _BIDI_WRITE_REDIRECTED_TYPE_URL:
                                redirect_proto = (
                                    BidiWriteObjectRedirectedError.deserialize(
                                        detail.value
                                    )
                                )
                                if redirect_proto.routing_token:
                                    self._routing_token = redirect_proto.routing_token
                                if redirect_proto.write_handle:
                                    self.write_handle = redirect_proto.write_handle
                                break
                    except Exception:
                        # Could not parse the error, ignore
                        pass

    async def open(
        self,
        retry_policy: Optional[AsyncRetry] = None,
        metadata: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        """Opens the underlying bidi-gRPC stream.

        :raises ValueError: If the stream is already open.

        """
        if self._is_stream_open:
            raise ValueError("Underlying bidi-gRPC stream is already open")

        if retry_policy is None:
            retry_policy = AsyncRetry(
                predicate=_is_write_retryable, on_error=self._on_open_error
            )
        else:
            original_on_error = retry_policy._on_error

            def combined_on_error(exc):
                self._on_open_error(exc)
                if original_on_error:
                    original_on_error(exc)

            retry_policy = retry_policy.with_predicate(
                _is_write_retryable
            ).with_on_error(combined_on_error)

        async def _do_open():
            print("In _do_open method")
            current_metadata = list(metadata) if metadata else []

            # Cleanup stream from previous failed attempt, if any.
            if self.write_obj_stream:
                if self._is_stream_open:
                    try:
                        await self.write_obj_stream.close()
                    except Exception:  # ignore cleanup errors
                        pass
                self.write_obj_stream = None
                self._is_stream_open = False

            self.write_obj_stream = _AsyncWriteObjectStream(
                client=self.client,
                bucket_name=self.bucket_name,
                object_name=self.object_name,
                generation_number=self.generation,
                write_handle=self.write_handle,
            )

            if self._routing_token:
                current_metadata.append(
                    ("x-goog-request-params", f"routing_token={self._routing_token}")
                )
                self._routing_token = None

            print("Current metadata in _do_open:", current_metadata)
            await self.write_obj_stream.open(
                metadata=current_metadata if metadata else None
            )

            if self.write_obj_stream.generation_number:
                self.generation = self.write_obj_stream.generation_number
            if self.write_obj_stream.write_handle:
                self.write_handle = self.write_obj_stream.write_handle
            if self.write_obj_stream.persisted_size is not None:
                self.persisted_size = self.write_obj_stream.persisted_size

            self._is_stream_open = True

        print("In open method, before retry_policy call")
        await retry_policy(_do_open)()


    async def append(
        self,
        data: bytes,
        retry_policy: Optional[AsyncRetry] = None,
        metadata: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        """Appends data to the Appendable object with automatic retries.

        calling `self.append` will append bytes at the end of the current size
        ie. `self.offset` bytes relative to the begining of the object.

        This method sends the provided `data` to the GCS server in chunks.
        and persists data in GCS at every `_DEFAULT_FLUSH_INTERVAL_BYTES` bytes
        or at the last chunk whichever is earlier. Persisting is done by setting
        `flush=True` on request.

        :type data: bytes
        :param data: The bytes to append to the object.

        :type retry_policy: :class:`~google.api_core.retry_async.AsyncRetry`
        :param retry_policy: (Optional) The retry policy to use for the operation.

        :type metadata: List[Tuple[str, str]]
        :param metadata: (Optional) The metadata to be sent with the request.

        :raises ValueError: If the stream is not open.
        """
        if not self._is_stream_open:
            raise ValueError("Stream is not open. Call open() before append().")
        if not data:
            return

        if retry_policy is None:
            retry_policy = AsyncRetry(predicate=_is_write_retryable)

        buffer = io.BytesIO(data)
        target_persisted_size = self.persisted_size + len(data)
        attempt_count = 0

        print("In append method")

        def send_and_recv_generator(requests: List[BidiWriteObjectRequest], state: dict[str, _WriteState], metadata: Optional[List[Tuple[str, str]]] = None):
            async def generator():
                print("In send_and_recv_generator")
                nonlocal attempt_count
                attempt_count += 1
                resp = None
                async with self._lock:
                    write_state = state["write_state"]
                    # If this is a retry or redirect, we must re-open the stream
                    if attempt_count > 1 or write_state.routing_token:
                        print("Re-opening the stream inside send_and_recv_generator with attempt_count:", attempt_count)
                        if self.write_obj_stream and self.write_obj_stream.is_stream_open:
                            await self.write_obj_stream.close()

                        self.write_obj_stream = self._stream_opener(write_handle=write_state.write_handle)
                        current_metadata = list(metadata) if metadata else []
                        if write_state.routing_token:
                            current_metadata.append(("x-goog-request-params", f"routing_token={write_state.routing_token}"))
                        await self.write_obj_stream.open(metadata=current_metadata if current_metadata else None)

                        self._is_stream_open = True
                        write_state.persisted_size = self.persisted_size
                        write_state.write_handle = self.write_handle

                    print("Sending requests in send_and_recv_generator")
                    # req_iter = iter(requests)

                    print("Starting to send requests")
                    for i, chunk_req in enumerate(requests):
                        if i == len(requests) - 1:
                            chunk_req.state_lookup = True
                        print("Sending chunk request")
                        await self.write_obj_stream.send(chunk_req)
                        print("Waiting to receive response")
                        print("Current persisted_size:", state["write_state"].persisted_size, "Target persisted_size:", target_persisted_size)

                    resp = await self.write_obj_stream.recv()
                    if resp:
                        if resp.persisted_size is not None:
                            self.persisted_size = resp.persisted_size
                            state["write_state"].persisted_size = resp.persisted_size
                        if resp.write_handle:
                            self.write_handle = resp.write_handle
                            state["write_state"].write_handle = resp.write_handle
                        print("Received response in send_and_recv_generator", resp)

                yield resp

                    # while state["write_state"].persisted_size < target_persisted_size:
                    #     print("Waiting to receive response")
                    #     print("Current persisted_size:", state["write_state"].persisted_size, "Target persisted_size:", target_persisted_size)
                    #     resp = await self.write_obj_stream.recv()
                    #     print("Received response in send_and_recv_generator", resp)
                    #     if resp is None:
                    #         break
                    #     yield resp
            return generator()

        # State initialization
        spec = _storage_v2.AppendObjectSpec(
            bucket=f"projects/_/buckets/{self.bucket_name}", object=self.object_name, generation=self.generation
        )
        write_state = _WriteState(spec, _MAX_CHUNK_SIZE_BYTES, buffer)
        write_state.write_handle = self.write_handle
        write_state.persisted_size = self.persisted_size
        write_state.bytes_sent = self.persisted_size

        print("Before creating retry manager")
        retry_manager = _BidiStreamRetryManager(_WriteResumptionStrategy(),
                                                lambda r, s: send_and_recv_generator(r, s, metadata))
        await retry_manager.execute({"write_state": write_state}, retry_policy)

        # Sync local markers
        self.write_obj_stream.persisted_size = write_state.persisted_size
        self.write_obj_stream.write_handle = write_state.write_handle


    async def simple_flush(self) -> None:
        """Flushes the data to the server.
        Please note: Unlike `flush` it does not do `state_lookup`

        :rtype: None

        :raises ValueError: If the stream is not open (i.e., `open()` has not
            been called).
        """
        if not self._is_stream_open:
            raise ValueError("Stream is not open. Call open() before simple_flush().")

        async with self._lock:
            await self.write_obj_stream.send(
                _storage_v2.BidiWriteObjectRequest(
                    flush=True,
                )
            )

    async def flush(self) -> int:
        """Flushes the data to the server.

        :rtype: int
        :returns: The persisted size after flush.

        :raises ValueError: If the stream is not open (i.e., `open()` has not
            been called).
        """
        if not self._is_stream_open:
            raise ValueError("Stream is not open. Call open() before flush().")

        async with self._lock:
            await self.write_obj_stream.send(
                _storage_v2.BidiWriteObjectRequest(
                    flush=True,
                    state_lookup=True,
                )
            )
            response = await self.write_obj_stream.recv()
            self.persisted_size = response.persisted_size
            self.offset = self.persisted_size
            return self.persisted_size

    async def close(self, finalize_on_close=False) -> Union[int, _storage_v2.Object]:
        """Closes the underlying bidi-gRPC stream.

        :type finalize_on_close: bool
        :param finalize_on_close: Finalizes the Appendable Object. No more data
          can be appended.

        rtype: Union[int, _storage_v2.Object]
        returns: Updated `self.persisted_size` by default after closing the
            bidi-gRPC stream. However, if `finalize_on_close=True` is passed,
            returns the finalized object resource.

        :raises ValueError: If the stream is not open (i.e., `open()` has not
            been called).

        """
        if not self._is_stream_open:
            raise ValueError("Stream is not open. Call open() before close().")

        if finalize_on_close:
            return await self.finalize()

        await self.write_obj_stream.close()

        self._is_stream_open = False
        self.offset = None
        return self.persisted_size

    async def finalize(self) -> _storage_v2.Object:
        """Finalizes the Appendable Object.

        Note: Once finalized no more data can be appended.
        This method is different from `close`. if `.close()` is called data may
        still be appended to object at a later point in time by opening with
        generation number.
        (i.e. `open(..., generation=<object_generation_number>)`.
        However if `.finalize()` is called no more data can be appended to the
        object.

        rtype: google.cloud.storage_v2.types.Object
        returns: The finalized object resource.

        :raises ValueError: If the stream is not open (i.e., `open()` has not
            been called).
        """
        if not self._is_stream_open:
            raise ValueError("Stream is not open. Call open() before finalize().")

        print("In finalize method")

        # async with self._lock:
        print("Sending finish_write request")
        await self.write_obj_stream.send(
            _storage_v2.BidiWriteObjectRequest(finish_write=True)
        )
        print("Waiting to receive response for finalize")
        response = await self.write_obj_stream.recv()
        print("Received response for finalize:")
        self.object_resource = response.resource
        self.persisted_size = self.object_resource.size
        await self.write_obj_stream.close()

        self._is_stream_open = False
        self.offset = None
        return self.object_resource

    @property
    def is_stream_open(self) -> bool:
        return self._is_stream_open

    # helper methods.
    async def append_from_string(self, data: str):
        """
        str data will be encoded to bytes using utf-8 encoding calling

        self.append(data.encode("utf-8"))
        """
        raise NotImplementedError("append_from_string is not implemented yet.")

    async def append_from_stream(self, stream_obj):
        """
        At a time read a chunk of data (16MiB) from `stream_obj`
        and call self.append(chunk)
        """
        raise NotImplementedError("append_from_stream is not implemented yet.")

    async def append_from_file(
        self, file_obj: BufferedReader, block_size: int = _DEFAULT_FLUSH_INTERVAL_BYTES
    ):
        """
        Appends data to an Appendable Object using file_handle which is opened
        for reading in binary mode.

        :type file_obj: file
        :param file_obj: A file handle opened in binary mode for reading.

        """
        while block := file_obj.read(block_size):
            await self.append(block)
