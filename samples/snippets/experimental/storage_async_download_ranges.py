from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)
from io import BytesIO
import asyncio
import argparse
import logging
from grpc._cython import cygrpc


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
)
logging.getLogger("grpc.aio._call").setLevel(logging.DEBUG)
# logging.getLogger(
#     "google.cloud.storage._experimental.asyncio.async_multi_range_downloader"
# ).setLevel(logging.DEBUG)


async def test_mrd_by_tasks(bucket_name, object_name, generation_number=None):
    # loop1 = asyncio.get_event_loop()
    # print("loop1 id ", id(loop1))
    # loop2 = cygrpc.get_working_loop()
    # print("loop2 id ", id(loop2))
    client = AsyncGrpcClient()._grpc_client

    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name, generation_number)
    await mrd.open()

    # mrd2 = AsyncMultiRangeDownloader(
    #     client, bucket_name, object_name, generation_number
    # )
    # await mrd2.open()

    my_buff1 = BytesIO()
    my_buff2 = BytesIO()
    my_buff3 = BytesIO()
    my_buff4 = BytesIO()
    my_buff5 = BytesIO()
    my_buff6 = BytesIO()
    my_buff7 = BytesIO()
    my_buff8 = BytesIO()
    ranges1 = [
        (0, 100, my_buff1),
        (100, 20, my_buff2),
        (200, 123, my_buff3),
        (300, 789, my_buff4),
    ]

    # ranges2 = [
    #     (200, 34, my_buff7),
    #     (300, 73, my_buff8),
    #     (0, 100, my_buff5),
    #     (100, 543, my_buff6),
    #     (1, 4324, BytesIO()),
    #     (343, 78, BytesIO()),
    # ]

    # This works fine !
    # _ = await mrd.download_ranges(ranges1, 1000)
    # _ = await mrd.download_ranges(ranges2, 2000)

    # This doesn't work, hangs in `self._cython_call.status()`
    # in `grpc/aio/_call.py`
    # but when kept under `with asyncio.timeout(30) .... ` it works
    # see implementation of `download_ranges` in `async_multi_range_downloader`
    #  how it's working with asyncio.timeout
    lock = asyncio.Lock()
    task1 = asyncio.create_task(mrd.download_ranges(ranges1, 1000, lock))
    # task2 = asyncio.create_task(mrd.download_ranges(ranges2, 2000, lock))
    print("task1 loopid ", id(task1._loop))
    # print("task2 loopid ", id(task2._loop))
    # _ = await asyncio.gather(task1, task2)

    print("downloading complete: Buffer details")
    for read_id, buffer in mrd.read_id_to_writable_buffer_dict.items():
        print(read_id, buffer.getbuffer().nbytes)

    # print("Buffer details for mrd2")
    # for read_id, buffer in mrd2.read_id_to_writable_buffer_dict.items():
    #     print(read_id, buffer.getbuffer().nbytes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, required=True)
    parser.add_argument("--object_name", type=str, required=True)
    parser.add_argument("--generation_number", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(
        test_mrd_by_tasks(args.bucket_name, args.object_name, args.generation_number),
        # debug=True,
    )
