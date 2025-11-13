# experimental poc - chandrasiri
import asyncio
from typing import Optional
from google.cloud import _storage_v2
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_abstract_object_stream import (
    _AsyncAbstractObjectStream,
)
from google.api_core.bidi_async import AsyncBidiRpc


class _AsyncWriteObjectStream(_AsyncAbstractObjectStream):
    """Class representing a gRPC bidi-stream for writing data from a GCS
      ``Appendable Object``.

    This class provides a unix socket-like interface to a GCS ``Object``, with
    methods like ``open``, ``close``, ``send``, and ``recv``.

    :type client: :class:`~google.cloud.storage._experimental.asyncio.async_grpc_client.AsyncGrpcClient.grpc_client`
    :param client: async grpc client to use for making API requests.

    :type bucket_name: str
    :param bucket_name: The name of the GCS ``bucket`` containing the object.

    :type object_name: str
    :param object_name: The name of the GCS ``Appendable Object`` to be write.

    :type generation_number: int
    :param generation_number: (Optional) If present, selects a specific revision of
                              this object. If None, a new object is created.

    :type write_handle: bytes
    :param write_handle: (Optional) An existing handle for writing the object.
                        If provided, opening the bidi-gRPC connection will be faster.
    """

    def __init__(
        self,
        client: AsyncGrpcClient.grpc_client,
        bucket_name: str,
        object_name: str,
        generation_number: Optional[int] = None,  # None means new object
        write_handle: Optional[bytes] = None,
    ) -> None:
        if client is None:
            raise ValueError("client must be provided")
        if bucket_name is None:
            raise ValueError("bucket_name must be provided")
        if object_name is None:
            raise ValueError("object_name must be provided")

        super().__init__(
            bucket_name=bucket_name,
            object_name=object_name,
            generation_number=generation_number,
        )
        self.client: AsyncGrpcClient.grpc_client = client
        self.write_handle: Optional[bytes] = write_handle

        self._full_bucket_name = f"projects/_/buckets/{self.bucket_name}"

        self.rpc = self.client._client._transport._wrapped_methods[
            self.client._client._transport.bidi_write_object
        ]

        self.metadata = (("x-goog-request-params", f"bucket={self._full_bucket_name}"),)
        self.socket_like_rpc: Optional[AsyncBidiRpc] = None
        self._is_stream_open: bool = False
        self.first_bidi_write_req = None
        self.persisted_size = 0
        self.object_resource: Optional[_storage_v2.Object] = None

    async def open(self) -> None:
        """Opening an object for write , should do it's state lookup
        to know what's the persisted size is.
        """
        raise NotImplementedError(
            "open() is not implemented yet in _AsyncWriteObjectStream"
        )

    async def close(self) -> None:
        """Closes the bidi-gRPC connection."""
        raise NotImplementedError(
            "close() is not implemented yet in _AsyncWriteObjectStream"
        )

    async def send(
        self, bidi_write_object_request: _storage_v2.BidiWriteObjectRequest
    ) -> None:
        """Sends a request message on the stream.

        Args:
            bidi_write_object_request (:class:`~google.cloud._storage_v2.types.BidiReadObjectRequest`):
                The request message to send. This is typically used to specify
                the read offset and limit.
        """
        raise NotImplementedError(
            "send() is not implemented yet in _AsyncWriteObjectStream"
        )

    async def recv(self) -> _storage_v2.BidiWriteObjectResponse:
        """Receives a response from the stream.

        This method waits for the next message from the server, which could
        contain object data or metadata.

        Returns:
            :class:`~google.cloud._storage_v2.types.BidiWriteObjectResponse`:
                The response message from the server.
        """
        raise NotImplementedError(
            "recv() is not implemented yet in _AsyncWriteObjectStream"
        )
