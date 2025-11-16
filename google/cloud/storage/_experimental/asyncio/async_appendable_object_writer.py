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
NOTE:
This is _experimental module for upcoming support for Rapid Storage.
(https://cloud.google.com/blog/products/storage-data-transfer/high-performance-storage-innovations-for-ai-hpc#:~:text=your%20AI%20workloads%3A-,Rapid%20Storage,-%3A%20A%20new)

APIs may not work as intended and are not stable yet. Feature is not
GA(Generally Available) yet, please contact your TAM (Technical Account Manager)
if you want to use these Rapid Storage APIs.

"""
from typing import Optional
from google.cloud import _storage_v2
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)
from google.cloud.storage._experimental.asyncio.async_write_object_stream import (
    _AsyncWriteObjectStream,
)


_MAX_CHUNK_SIZE_BYTES = 2 * 1024 * 1024  # 2 MiB
_MAX_BUFFER_SIZE_BYTES = 16 * 1024 * 1024  # 8 MiB


class AsyncAppendableObjectWriter:
    """Class for appending data to a GCS Appendable Object asynchronously."""

    def __init__(
        self,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: str,
        object_name: str,
        generation=None,
        write_handle=None,
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

        :type generation: int
        :param generation: (Optional) If present, selects a specific revision of
                            that object.
                            If None, a new object is created.
                            If None and Object already exists then it'll will be
                            overwritten.

        :type write_handle: bytes
        :param write_handle: (Optional) An existing handle for writing the object.
                            If provided, opening the bidi-gRPC connection will be faster.
        """
        self.client = client
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.write_handle = write_handle
        self.generation = generation

        self.write_obj_stream = _AsyncWriteObjectStream(
            client=self.client,
            bucket_name=self.bucket_name,
            object_name=self.object_name,
            generation_number=self.generation,
            write_handle=self.write_handle,
        )
        self._is_stream_open: bool = False
        self.offset: Optional[int] = None
        self.persisted_size: Optional[int] = None

    async def state_lookup(self) -> int:
        """Returns the persisted_size

        :rtype: int
        :returns: persisted size.
        """
        await self.write_obj_stream.send(
            _storage_v2.BidiWriteObjectRequest(
                state_lookup=True,
            )
        )
        response = await self.write_obj_stream.recv()
        self.persisted_size = response.persisted_size
        return self.persisted_size

    async def open(self) -> None:
        """Opens the underlying bidi-gRPC stream."""
        if self._is_stream_open:
            raise ValueError("Underlying bidi-gRPC stream is already open")

        await self.write_obj_stream.open()
        self._is_stream_open = True
        if self.generation is None:
            self.generation = self.write_obj_stream.generation_number
        self.write_handle = self.write_obj_stream.write_handle

        # Update self.persisted_size
        _ = await self.state_lookup()

    async def append(self, data: bytes):
        if not self._is_stream_open:
            raise ValueError("Stream is not open. Call open() before append().")
        total_bytes = len(data)
        if total_bytes == 0:
            # TODO: add warning.
            return
        if self.offset is None:
            assert self.persisted_size is not None
            self.offset = self.persisted_size

        for i in range(0, total_bytes, _MAX_BUFFER_SIZE_BYTES):
            buffer_data = data[i : i + _MAX_BUFFER_SIZE_BYTES]
            buffer_size = len(buffer_data)
            curr_index = 0
            while curr_index < buffer_size:
                end_index = min(curr_index + _MAX_CHUNK_SIZE_BYTES, buffer_size)
                chunk = data[curr_index:end_index]
                await self.write_obj_stream.send(
                    _storage_v2.BidiWriteObjectRequest(
                        write_offset=self.offset,
                        checksummed_data=_storage_v2.ChecksummedData(content=chunk),
                    )
                )
                curr_index = end_index
                self.offset += len(chunk)
            # if buffer is full, flush to persist data.
            if buffer_size == _MAX_BUFFER_SIZE_BYTES:
                await self.flush()

    async def flush(self) -> int:
        """Flushes the data to the server.

        :rtype: int
        :returns: The persisted size after flush.
        """
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

    async def close(self, finalize_on_close=False) -> int:
        """Returns persisted_size"""
        if finalize_on_close:
            await self.finalize()

        await self.write_obj_stream.close()
        self._is_stream_open = False
        self.offset = None

    async def finalize(self) -> _storage_v2.Object:
        """Finalizes the Appendable Object.

        Note: Once finalized no more data can be appended.

        rtype: google.cloud.storage_v2.types.Object
        returns: The finalized object resource.
        """
        await self.write_obj_stream.send(
            _storage_v2.BidiWriteObjectRequest(finish_write=True)
        )
        response = await self.write_obj_stream.recv()
        self.object_resource = response.resource

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

    async def append_from_file(self, file_path: str):
        """Create a file object from `file_path` and call append_from_stream(file_obj)"""
        raise NotImplementedError("append_from_file is not implemented yet.")


async def test_aaow():
    import os
    import time

    client = AsyncGrpcClient().grpc_client
    writer = AsyncAppendableObjectWriter(
        client=client,
        bucket_name="chandrasiri-rs",
        object_name="code-test-20251116-1",
        generation=1763299631619231,
    )
    await writer.open()
    print("finished open()", writer.persisted_size)
    # print("1st state lookup", await writer.state_lookup())
    # # start_time = time.monotonic_ns()
    # num_bytes_to_append = 100 * 1024 * 1024
    # await writer.append(os.urandom(num_bytes_to_append))
    # # for i in range(100):
    # await writer.flush()
    # print(f"finished appending {num_bytes_to_append} byte")
    # await asyncio.sleep(1)
    # end_time = time.monotonic_ns()
    # duration_secs = (end_time - start_time) / 1e9
    # print(f"finished appending 100*200MiB  in {duration_secs} seconds")
    # print("Throuput is ", (100 * 200) / duration_secs, " MiB/s")
    # print("finished appending 1 byte, sleeping for 60+ seconds")
    # print("2nd state lookup", await writer.state_lookup())

    return


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_aaow())
