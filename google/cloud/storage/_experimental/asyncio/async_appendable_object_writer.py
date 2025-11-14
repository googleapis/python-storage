from typing import Optional
from google.cloud import _storage_v2
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)
from google.cloud.storage._experimental.asyncio.async_write_object_stream import (
    _AsyncWriteObjectStream,
)


class AsyncAppendableObjectWriter:
    def __init__(
        self,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: str,
        object_name: str,
        generation=None,
        write_handle=None,
    ):
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

    async def state_lookup(self):
        """Returns the persisted_size."""
        await self.write_obj_stream.send(
            _storage_v2.BidiWriteObjectRequest(
                state_lookup=True,
            )
        )
        return await self.write_obj_stream.recv()

    async def open(self) -> None:
        """Opens the underlying bidi-gRPC stream."""
        raise NotImplementedError("open is not implemented yet.")

    async def append(self, data: bytes):
        raise NotImplementedError("append is not implemented yet.")

    async def flush(self) -> int:
        """Returns persisted_size"""
        raise NotImplementedError("flush is not implemented yet.")

    async def close(self, finalize_on_close=False) -> int:
        """Returns persisted_size"""
        raise NotImplementedError("close is not implemented yet.")

    async def finalize(self) -> int:
        """Returns persisted_size
        Note: Once finalized no more data can be appended.
        """
        raise NotImplementedError("finalize is not implemented yet.")

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
