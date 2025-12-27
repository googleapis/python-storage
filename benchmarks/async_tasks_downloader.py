import asyncio
import time
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)

BUCKET_NAME = "chandrasiri-rs"
OBJECT_SIZE = 100 * 1024 * 1024


async def download_object_async(bucket_name, object_name, client=None):
    """Downloads a single object."""
    if client is None:
        client = AsyncGrpcClient().grpc_client

    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()
    buffer = BytesIO()
    await mrd.download_ranges(read_ranges=[(0, 0, buffer)])
    await mrd.close()

    assert buffer.getbuffer().nbytes == OBJECT_SIZE

    # Save the downloaded object to a local file
    # with open(object_name, "wb") as f:
    #     f.write(buffer.getvalue())

    # print(f"Finished downloading {object_name}")


async def download_objects_pool(start_obj_num, end_obj_num):
    """ """

    client = AsyncGrpcClient().grpc_client
    tasks = []
    pool_start_time = time.monotonic_ns()
    for obj_num in range(start_obj_num, end_obj_num):
        tasks.append(
            asyncio.create_task(
                download_object_async(BUCKET_NAME, f"para_64-{obj_num}", client=client)
            )
        )

    await asyncio.gather(*tasks)
    pool_end_time = time.monotonic_ns()
    print(
        f"{end_obj_num - start_obj_num} tasks done! in {(pool_end_time - pool_start_time) / (10**9)}s"
    )


async def main():
    """Main function to orchestrate parallel downloads using threads."""
    num_objects = 1000
    pool_size = 100
    start_time = time.monotonic_ns()

    for i in range(0, num_objects, pool_size):
        await download_objects_pool(i, i + pool_size)
    end_time = time.monotonic_ns()
    print(
        f"FINSHED: total bytes downloaded - {num_objects*OBJECT_SIZE} in time {(end_time - start_time) / (10**9)}s"
    )


if __name__ == "__main__":
    asyncio.run(main())
