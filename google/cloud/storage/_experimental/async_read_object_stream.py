from google.cloud.storage._experimental.async_abstract_object_stream import (
    AsyncAbstractObjectStream,
)
from bidi_async import AsyncBidiRpc
import asyncio
import argparse
from async_grpc_client import AsyncGrpcClient
from google.cloud import _storage_v2 as storage_v2


"""
Mrr_generic(bucket, obj,gen=None, read_handle=None)
mrr = Mrr(bucket, obj, gen)

mrr = Mrr(bucket, obj)
mrr = Mrr.create_from(bucket, obj)
        Mrr_generic(bucket, obj,gen=None, read_handle=None)
            * set attributes
            * instantiate read_object_strea
    * async stream.open
mrr = Mrr(read_handle)
mrr = 

"""


class AsynReadObjectStream(AsyncAbstractObjectStream):
    def __init__(
        self,
        client,
        bucket_name=None,
        object_name=None,
        generation_number=None,
        read_handle=None,  # open with rea
    ):
        super().__init__(
            bucket_name=bucket_name,
            object_name=object_name,
            generation_number=generation_number,
        )
        self.client = client
        j
        self.bucket_name = bucket_name
        self._full_bucket_name = f"projects/_/buckets/{bucket_name}"
        self.object_name = object_name
        self.generation_number = generation_number
        self.read_handle = read_handle

        # can this interface be changed tmrw ? (not accounting for that)
        # self.rpc = self.client.get_bidi_rpc_str_str_mc()  # expose this func in GAPIC
        self.rpc = self.client._client._transport._wrapped_methods[
            self._client._transport.bidi_read_object
        ]
        first_bidi_read_req = storage_v2.BidiReadObjectRequest(
            read_object_spec=storage_v2.BidiReadObjectSpec(
                bucket=self._full_bucket_name, object=object_name
            ),
        )
        self.metadata = (("x-goog-request-params", f"bucket={self._full_bucket_name}"),)
        self.socket_like_rpc = AsyncBidiRpc(
            self.rpc, initial_request=first_bidi_read_req, metadata=self.metadata
        )

    async def open(self) -> None:
        """
        1 send & 1 recv()

        """
        await self.socket_like_rpc.open()  # this is actually 1 send
        response = await self.socket_like_rpc.recv()
        print(response)

        return
        # return await super().open()

    async def close(self):
        return await super().close()

    async def send(self, bidi_read_object_request):
        self.socket_like_rpc.send(bidi_read_object_request)
        """
        1. what if this fails ? 
        2. calculate checksum and send data
            A: you don't have to calcuate checksum here. since it's read da! DF
        
        """

        return

    async def recv(self):
        bidi_read_object_response = self.socket_like_rpc.recv()
        """
        P0 - get this working.
        1. what if this fails ?
            what kind of error ? 
            existing retry wrapper ? from gapic
        2. data is already checksumm'ed ,
            you calcuated the checksum , verify and return. If verification fails raise.
        
        3. traces ? 

        4. what if decompressive transcoding ?


        """
        return bidi_read_object_response


async def test(bucket_name, object_name):
    client = AsyncGrpcClient()._grpc_client
    async_read_obj_str = AsynReadObjectStream(
        client, bucket_name=bucket_name, object_name=object_name
    )
    await async_read_obj_str.open()

    # create bidi proto 'n' requests
    # n = 10
    # for i in range(n):
    #     await async_read_obj_str.send()

    # for i in range(n):
    #     await async_read_obj_str.recv()

    # pass


if __name__ == "__main__":
    """
    1. import argparse
    2. create parser
    3. add args

    4. parse args
    """
    parser = argparse.ArgumentParser()
    argparse.add_argument(
        "--bucket_name", help="The name of the GCS bucket to upload to."
    )
    argparse.add_argument("--object_name", help="Object name")
    args = parser.parse_args()

    asyncio.run(test(bucket_name=args.bucket_name, object_name=args.object_name))
    # test()
