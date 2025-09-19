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

from typing import Any, List, Optional, Tuple

from google.cloud.storage._experimental.asyncio.async_read_object_stream import (
    _AsyncReadObjectStream,
)
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)

from io import BytesIO
from google.cloud import _storage_v2
import sys
import asyncio


_MAX_READ_RANGES_PER_BIDI_READ_REQUEST = 100


class AsyncMultiRangeDownloader:
    """Provides an interface for downloading multiple ranges of a GCS object concurrently."""

    @classmethod
    async def create_mrd(
        cls,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: str,
        object_name: str,
        generation_number: Optional[int] = None,
    ) -> AsyncMultiRangeDownloader:
        """Asynchronously creates and initializes a MultiRangeDownloader.

        This factory method creates an instance of MultiRangeDownloader and
        opens the underlying bidi-gRPC connection.

        Args:
            client (AsyncGrpcClient.grpc_client): The asynchronous client to use for making API requests.
            bucket_name (str): The name of the bucket containing the object.
            object_name (str): The name of the object to be read.
            generation_number (int, optional): If present, selects a specific
                                               revision of this object.

        Returns:
            MultiRangeDownloader: An initialized MultiRangeDownloader instance.
        """
        mrd = cls(client, bucket_name, object_name, generation_number)
        await mrd.open()
        return mrd

    @classmethod
    def create_mrd_from_read_handle(
        cls, client: AsyncGrpcClient.grpc_client, read_handle: bytes
    ) -> AsyncMultiRangeDownloader:
        """Creates a MultiRangeDownloader from an existing read handle.

        Args:
            client (AsyncGrpcClient.grpc_client): The asynchronous client to use for making API requests.
            read_handle (bytes): An existing handle for reading the object.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError("TODO")

    def __init__(
        self,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: Optional[str] = None,
        object_name: Optional[str] = None,
        generation_number: Optional[int] = None,
        read_handle: Optional[bytes] = None,
    ) -> None:
        """Initializes a MultiRangeDownloader.

        Args:
            client (AsyncGrpcClient.grpc_client): The asynchronous client to use for making API requests.
            bucket_name (str, optional): The name of the bucket. Defaults to None.
            object_name (str, optional): The name of the object. Defaults to None.
            generation_number (int, optional): The generation number of the object.
                                               Defaults to None.
            read_handle (bytes, optional): An existing read handle. Defaults to None.
        """
        self.client = client
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.generation_number = generation_number
        self.read_handle = read_handle
        self.read_obj_str: _AsyncReadObjectStream

    async def open(self) -> None:
        """Opens the bidi-gRPC connection to read from the object.

        This method initializes and opens an `_AsyncReadObjectStream` to
        establish a connection for downloading. It also retrieves the
        generation number and read handle if they are not already set.
        """
        self.read_obj_str = _AsyncReadObjectStream(
            client=self.client,
            bucket_name=self.bucket_name,
            object_name=self.object_name,
            generation_number=self.generation_number,
            read_handle=self.read_handle,
        )
        await self.read_obj_str.open()
        if self.generation_number is None:
            self.generation_number = self.read_obj_str.generation_number
        self.read_handle = self.read_obj_str.read_handle
        return

    async def download_ranges(self, read_ranges: List[Tuple[int, int, BytesIO]]) -> Any:
        """Downloads multiple byte ranges from the object into the buffers
        provided by user.

        Args:
            read_ranges (List[Tuple[int, int, BytesIO]]): A list of tuples, where each
            tuple represents a byte range (start_byte, end_byte, buffer) to download.

        """
        if len(read_ranges) > 1000:
            raise Exception("Invalid Input - ranges cannot be more than 1000")

        read_id_to_writable_buffer_dict = {}
        for i in range(0, len(read_ranges), _MAX_READ_RANGES_PER_BIDI_READ_REQUEST):
            read_range_segment = read_ranges[
                i : i + _MAX_READ_RANGES_PER_BIDI_READ_REQUEST
            ]

            read_ranges_for_bidi_req = []
            for j, read_range in enumerate(read_range_segment):
                # generate read_id
                read_id = i + j
                read_id_to_writable_buffer_dict[read_id] = read_range[2]
                read_ranges_for_bidi_req.append(
                    _storage_v2.ReadRange(
                        read_offset=read_range[0],
                        read_length=read_range[1] - read_range[0],  # end - start
                        read_id=read_id,
                    )
                )
            print(read_ranges_for_bidi_req)
            await self.read_obj_str.send(
                _storage_v2.BidiReadObjectRequest(read_ranges=read_ranges_for_bidi_req)
            )
        while len(read_id_to_writable_buffer_dict) > 0:
            response = await self.read_obj_str.recv()
            if response is None:
                print("None response received, something went wrong.")
                sys.exit(1)
            for object_data_range in response.object_data_ranges:

                if object_data_range.read_range is None:
                    raise Exception("Invalid response, read_range is None")

                data = object_data_range.checksummed_data.content
                # bytes_received_in_curr_res = object_data_range.read_range.read_length
                read_id = object_data_range.read_range.read_id
                buffer = read_id_to_writable_buffer_dict[read_id]
                buffer.write(data)
                print(
                    "for read_id ",
                    read_id,
                    data,
                    object_data_range.checksummed_data.crc32c,
                )
                if object_data_range.range_end:
                    del read_id_to_writable_buffer_dict[
                        object_data_range.read_range.read_id
                    ]


async def test_mrd():
    client = AsyncGrpcClient()._grpc_client
    mrd = await AsyncMultiRangeDownloader.create_mrd(
        client, bucket_name="chandrasiri-rs", object_name="test_open9"
    )
    my_buff1 = BytesIO()
    my_buff2 = BytesIO()
    my_buff3 = BytesIO()
    my_buff4 = BytesIO()
    buffers = [my_buff1, my_buff2, my_buff3, my_buff4]
    await mrd.download_ranges(
        [
            (0, 100, my_buff1),
            (100, 200, my_buff2),
            (200, 300, my_buff3),
            (300, 400, my_buff4),
        ]
    )
    for buff in buffers:
        print("downloaded bytes", buff.getbuffer().nbytes)


if __name__ == "__main__":
    asyncio.run(test_mrd())
