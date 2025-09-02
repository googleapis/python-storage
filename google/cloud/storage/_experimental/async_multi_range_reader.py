"""
Mrd_generic(bucket, obj,gen=None, read_handle=None)
mrd = Mrd(bucket, obj, gen)

mrd = Mrd(bucket, obj)
mrd = Mrd.create_from(client, bucket, obj)
        Mrd_generic(bucket, obj,gen=None, read_handle=None)
            * set attributes
            * instantiate read_object_strea
    * async stream.open
mrd = Mrd(read_handle)
mrd.download_ranges([(range_start, range_end, buf)])

mrr = await MultiRangeDownloader.create_mrd(client, bucket, obj)
await mrr.download_ranges([(range_start, range_end, buf)])


"""

from async_read_object_stream import AsyncReadObjectStream
from async_grpc_client import AsyncGrpcClient
from io import BytesIO
from google.cloud import _storage_v2
import sys
import asyncio


class MultiRangeDownloader:

    @classmethod
    async def create_mrd(cls, client, bucket_name, object_name, generation_number=None):
        # inti
        # async mrd.open()
        mrd = cls(client, bucket_name, object_name, generation_number)
        await mrd.open()
        return mrd

    @classmethod
    def create_mrd_from_read_handle(cls, client, read_handle):
        raise NotImplementedError("TODO")

    def __init__(
        self,
        client,
        bucket_name=None,
        object_name=None,
        generation_number=None,
        read_handle=None,  # open with rea
    ):
        self.client = client
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.generation_number = generation_number
        self.read_handle = read_handle

    async def open(self):
        self.read_obj_str = AsyncReadObjectStream(
            client=self.client,
            bucket_name=self.bucket_name,
            object_name=self.object_name,
            generation_number=self.generation_number,
            read_handle=self.read_handle,
        )
        await self.read_obj_str.open()
        pass

    async def download_ranges(self, ranges):
        first_range = ranges[0]
        start = first_range[0]
        end = first_range[1]
        buffer = first_range[2]
        # create bidiReadReq
        read_id = 1
        await self.read_obj_str.send(
            _storage_v2.BidiReadObjectRequest(
                read_ranges=[
                    _storage_v2.ReadRange(
                        read_offset=start, read_length=end, read_id=read_id
                    )
                ]
            )
        )
        # while read_end is not reached.
        read_ids_set = set()
        read_ids_set.add(read_id)
        bytes_received = 0
        while len(read_ids_set) > 0:
            response = await self.read_obj_str.recv()
            if response is None:
                print("None response received, something went wrong.")
                sys.exit(1)
            for object_data_chunk in response.object_data_ranges:
                data = object_data_chunk.checksummed_data.content
                buffer.write(data)
                print(data)
                print(object_data_chunk.checksummed_data.crc32c)

                if object_data_chunk.read_range is not None:
                    # bytes downloaded in this response.
                    curr_iter_bytes = object_data_chunk.read_range.read_length
                    bytes_received += curr_iter_bytes
                    # if curr_iter_bytes != 2 * 1024 * 1024:
                    #     print(
                    #         "bytes received in current iter, for read_id",
                    #         curr_iter_bytes,
                    #         object_data_chunk.read_range.read_id,
                    #     )
                    # print(
                    #     "bytes received in current iter, for read_id",
                    #     curr_iter_bytes,
                    #     object_data_chunk.read_range.read_id,
                    # )

                if (
                    object_data_chunk.range_end is not None
                    and object_data_chunk.range_end
                ):
                    # print(
                    #     f"Read ID {object_data_chunk.read_range.read_id} completed."
                    # )
                    read_ids_set.remove(object_data_chunk.read_range.read_id)
        print("downloaded bytes", bytes_received)

        # pass


async def test_mrd():
    client = AsyncGrpcClient()._grpc_client
    mrd = await MultiRangeDownloader.create_mrd(
        client, bucket_name="chandrasiri-rs", object_name="test_open9"
    )
    my_buff = BytesIO()
    await mrd.download_ranges([(0, 10, my_buff)])
    # print()
    print("downloaded bytes", my_buff.getbuffer().nbytes)


if __name__ == "__main__":
    asyncio.run(test_mrd())
