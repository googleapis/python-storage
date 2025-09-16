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
import uuid

_MAX_READ_RANGES_PER_BIDI_READ_REQUEST = 100


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
        if self.generation_number is None:
            self.generation_number = self.read_obj_str.generation_number
        self.read_handle = self.read_obj_str.read_handle
        return

    async def download_ranges(self, read_ranges):
        """
        1.user can provide any number of ranges upto 1000.
        2.


        """
        # > 1000 not supported yet.
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
            # read_ranges_for_bidi_req = [
            #     _storage_v2.ReadRange(
            #         read_offset=x[0], read_length=x[1], read_id=read_id
            #     )
            # ]
            # first_range = read_ranges[0]
            # start = first_range[0]
            # end = first_range[1]
            # buffer = first_range[2]
            # # create bidiReadReq
            # read_id = 1
            print(read_ranges_for_bidi_req)
            await self.read_obj_str.send(
                _storage_v2.BidiReadObjectRequest(read_ranges=read_ranges_for_bidi_req)
            )
        # while read_end is not reached.
        # read_ids_set = set()
        # read_ids_set.add(read_id)
        # bytes_received = 0
        # while len(read_ids_set) > 0:
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
        # print("downloaded bytes", bytes_received)

        # pass


async def test_mrd():
    client = AsyncGrpcClient()._grpc_client
    mrd = await MultiRangeDownloader.create_mrd(
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
    # print("this is the generation, read handle", mrd.generation_number, mrd.read_handle)
    for buff in buffers:
        print("downloaded bytes", buff.getbuffer().nbytes)


if __name__ == "__main__":
    asyncio.run(test_mrd())
