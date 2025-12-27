
"""
Docstring for tests.perf.microbenchmarks.test_reads

File for benchmarking zonal reads (i.e. downloads)

1. 1 object 1 coro with variable chunk_size 

calculate latency, throughput, etc for downloads.


"""
import os
import time
import asyncio
import math
from io import BytesIO

import pytest
from google.api_core import exceptions
from google.cloud.storage.blob import Blob

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
from tests.perf.microbenchmarks.conftest import (
    # publish_benchmark_extra_info,
    # publish_multi_process_benchmark_extra_info,
    publish_resource_metrics,
)
# from tests.perf.microbenchmarks.config import RAPID_ZONAL_BUCKET, STANDARD_BUCKET
# from tests.perf.microbenchmarks import config
# from functools import partial

# Pytest-asyncio mode needs to be auto
pytest_plugins = "pytest_asyncio"

OBJECT_SIZE = 100 * (1024 ** 2)  # 1 GiB
UPLOAD_CHUNK_SIZE = 128 * 1024 * 1024
DOWNLOAD_CHUNK_SIZES = [
    # 4 * 1024 * 1024,
    # 16 * 1024 * 1024,
    # 32 * 1024 * 1024,
    100 * 1024 * 1024,
]



async def _download_one_async(
    async_grpc_client, bucket_name, object_name, download_size, chunk_size
):
    """
    Helper function to UPLOAD and then DOWNLOAD a single object asynchronously.
    This is the function that will be benchmarked.
    """


    # DOWNLOAD
    mrd = AsyncMultiRangeDownloader(async_grpc_client, bucket_name, object_name)
    await mrd.open()

    output_buffer = BytesIO()
    # download in chunks of `chunk_size`
    offset = 0
    output_buffer = BytesIO()
    while offset < download_size:
        bytes_to_download = min(chunk_size, download_size - offset)
        await mrd.download_ranges([(offset, bytes_to_download, output_buffer)])
        offset += bytes_to_download

    assert output_buffer.getbuffer().nbytes == download_size, f"downloaded size incorrect for {object_name}"
    print('downloaded bytes', output_buffer.getbuffer().nbytes)

    await mrd.close()



async def create_client():
    """Initializes async client and gets the current event loop."""
    return AsyncGrpcClient().grpc_client

async def upload_appendable_object(client, bucket_name, object_name, object_size, chunk_size):
    
    writer = AsyncAppendableObjectWriter(client, bucket_name, object_name)
    await writer.open()
    uploaded_bytes = 0
    while uploaded_bytes < object_size:
        bytes_to_upload = min(chunk_size, object_size - uploaded_bytes)
        await writer.append(os.urandom(bytes_to_upload))
        uploaded_bytes += bytes_to_upload
    await writer.close(finalize_on_close=False)
    # print('uploading took', time.)




def my_setup(loop, client, bucket_name: str, object_name: str, upload_size: int, chunk_size: int):
    """
    1. create a async method , name it my_setup_async
    2. call that method , 
        "my_setup_async" should initialize client.
        get the event_loop
        return client, event_loop
    3. this method should return client, event_loop
    
    """

    # client = loop.run_until_complete(create_client())


    loop.run_until_complete(upload_appendable_object(client, bucket_name, object_name, upload_size, chunk_size))
    # return client

def download_object(loop, client, bucket_name, object_name, download_size, chunk_size):
    loop.run_until_complete(_download_one_async(client, bucket_name, object_name, download_size, chunk_size))








@pytest.mark.parametrize("chunk_size", DOWNLOAD_CHUNK_SIZES)
# params - num_rounds or env var ? 
def test_read_one_object_one_stream(benchmark, chunk_size, storage_client, blobs_to_delete, monitor):
    """
    this test should use pytest-benchmark, 

    target_function should be `download_object`
    setup function should be `my_setup`
    no teardown function for now.
    
    """
    benchmark.extra_info["object_size"] = OBJECT_SIZE
    benchmark.extra_info["chunk_size"] = chunk_size

    bucket_name = "chandrasiri-rs"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = loop.run_until_complete(create_client())

    def setup_for_benchmark():
        start_time = time.time()
        # upload num_rounds of objects all at once.
        object_name = f"benchmark-object-cs-{os.urandom(4).hex()}"
        my_setup(loop, client, bucket_name, object_name, OBJECT_SIZE, chunk_size)
        end_time = time.time()
        print(f"\nSetup time: {end_time - start_time:.4f} seconds")
        return (loop, client, bucket_name, object_name, OBJECT_SIZE, chunk_size), {}
    
    def teardown(loop, client, bucket_name, object_name, OBJECT_SIZE, chunk_size):
        # _, _, _, object_name, _, _ = target_args

        # Clean up; use json client (i.e. `storage_client` fixture) to delete.
        blobs_to_delete.append(storage_client.bucket(bucket_name).blob(object_name))
        

    try:
        with monitor() as m:
            benchmark.pedantic(
            download_object,
            setup=setup_for_benchmark,
            teardown=teardown,
            iterations=1,
            rounds=10,
        )
    finally:
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()

    min_throughput = (OBJECT_SIZE / (1024 * 1024)) / benchmark.stats['max']
    max_throughput = (OBJECT_SIZE / (1024 * 1024)) / benchmark.stats['min']
    mean_throughput = (OBJECT_SIZE / (1024 * 1024)) / benchmark.stats['mean']
    median_throughput = (OBJECT_SIZE / (1024 * 1024)) / benchmark.stats['median']

    benchmark.extra_info["throughput_MiB_s_min"] = min_throughput
    benchmark.extra_info["throughput_MiB_s_max"] = max_throughput
    benchmark.extra_info["throughput_MiB_s_mean"] = mean_throughput
    benchmark.extra_info["throughput_MiB_s_median"] = median_throughput

    print(f"\nThroughput Statistics (MiB/s):")
    print(f"  Min:    {min_throughput:.2f} (from max time)")
    print(f"  Max:    {max_throughput:.2f} (from min time)")
    print(f"  Mean:   {mean_throughput:.2f} (approx, from mean time)")
    print(f"  Median: {median_throughput:.2f} (approx, from median time)")

    # Get benchmark name, rounds, and iterations
    name = benchmark.name
    rounds = benchmark.stats['rounds']
    iterations = benchmark.stats['iterations']

    # Header for throughput table
    header = "\n\n" + "-" * 125 + "\n"
    header += "Throughput Benchmark (MiB/s)\n"
    header += "-" * 125 + "\n"
    header += f"{'Name':<50} {'Min':>10} {'Max':>10} {'Mean':>10} {'StdDev':>10} {'Median':>10} {'Rounds':>8} {'Iterations':>12}\n"
    header += "-" * 125

    # Data row for throughput table
    # The table headers (Min, Max) refer to the throughput values.
    row = f"{name:<50} {min_throughput:>10.4f} {max_throughput:>10.4f} {mean_throughput:>10.4f} {'N/A':>10} {median_throughput:>10.4f} {rounds:>8} {iterations:>12}"

    print(header)
    print(row)
    print("-" * 125)

    publish_resource_metrics(benchmark, m)


#  def run_test():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     try:
#         client = my_setup(loop, 'chandrasiri-rs', 'test-loop2', 100*1024*1024, 16*1024*1024)
#         download_object(loop, client, 'chandrasiri-rs', 'test-loop2', 100*1024*1024, 16*1024*1024)
#     finally:
#         tasks = asyncio.all_tasks(loop=loop)
#         for task in tasks:
#             task.cancel()
#         loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
#         loop.close()

# if __name__ == "__main__":
#     run_test()