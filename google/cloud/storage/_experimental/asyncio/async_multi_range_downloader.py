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
            read_ranges (List[Tuple[int, int]]): A list of tuples, where each
            tuple represents a byte range (start_byte, end_byte, buffer) to download.


        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError("TODO")
