import asyncio
import time
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool


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

    print(f"Finished downloading {object_name}")


async def download_objects_pool(start_obj_num, end_obj_num):
    """ """
    print(f"starting for {start_obj_num}, {end_obj_num}")

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
        f"for {start_obj_num} , {end_obj_num}, {end_obj_num - start_obj_num} tasks done! in {(pool_end_time - pool_start_time) / (10**9)}s"
    )


def async_runner(start_obj_num, end_obj_num):
    asyncio.run(download_objects_pool(start_obj_num, end_obj_num))


def main():
    num_object = 3000
    process_count = 60
    objects_per_process = num_object // process_count  # 150
    args = []
    start_obj_num = 0
    for _ in range(process_count):
        args.append((start_obj_num, start_obj_num + objects_per_process))
        start_obj_num += objects_per_process
    # print(f"start {process_count} proc")
    start_time_proc = time.monotonic_ns()
    print(args, len(args))

    with Pool(processes=process_count) as pool:
        results = pool.starmap(async_runner, args)
    end_time_proc = time.monotonic_ns()

    print(
        f"TOTAL: bytes - {num_object*OBJECT_SIZE}, time: {(end_time_proc - start_time_proc) / (10**9)}s"
    )
    print(
        f"Throuput: {num_object*OBJECT_SIZE /((end_time_proc - start_time_proc) / (10**9))*10**-6} MBps"
    )


if __name__ == "__main__":
    main()
