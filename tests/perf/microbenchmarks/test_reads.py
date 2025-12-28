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
from tests.perf.microbenchmarks._utils import publish_benchmark_extra_info
from tests.perf.microbenchmarks.conftest import (
    # publish_multi_process_benchmark_extra_info,
    publish_resource_metrics,
)

# from tests.perf.microbenchmarks.config import RAPID_ZONAL_BUCKET, STANDARD_BUCKET
import tests.perf.microbenchmarks.config as config


# from functools import partial

# Pytest-asyncio mode needs to be auto
pytest_plugins = "pytest_asyncio"

# OBJECT_SIZE = 1024 * (1024**2)  # 1 GiB
UPLOAD_CHUNK_SIZE = 128 * 1024 * 1024
DOWNLOAD_CHUNK_SIZES = [
    # 4 * 1024 * 1024,
    # 16 * 1024 * 1024,
    # 32 * 1024 * 1024,
    64
    * 1024
    * 1024,
]

all_zonal_params = config._get_params()
all_regional_params = config._get_params(bucket_type_filter="regional")


async def _download_one_async(async_grpc_client, object_name, other_params):

    download_size = other_params.file_size_bytes
    chunk_size = other_params.chunk_size_bytes

    # DOWNLOAD
    mrd = AsyncMultiRangeDownloader(
        async_grpc_client, other_params.bucket_name, object_name
    )
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


async def upload_appendable_object(
    client, bucket_name, object_name, object_size, chunk_size
):
    writer = AsyncAppendableObjectWriter(client, bucket_name, object_name)
    await writer.open()
    uploaded_bytes = 0
    while uploaded_bytes < object_size:
        bytes_to_upload = min(chunk_size, object_size - uploaded_bytes)
        await writer.append(os.urandom(bytes_to_upload))
        uploaded_bytes += bytes_to_upload
    await writer.close(finalize_on_close=False)
    # print('uploading took', time.)


def my_setup(
    loop, client, bucket_name: str, object_name: str, upload_size: int, chunk_size: int
):
    loop.run_until_complete(
        upload_appendable_object(
            client, bucket_name, object_name, upload_size, chunk_size
        )
    )


def download_one_object_wrapper(loop, client, filename, other_params):
    loop.run_until_complete(_download_one_async(client, filename, other_params))


@pytest.mark.parametrize(
    "workload_params",
    all_zonal_params["read_seq_single_file"],
    indirect=True,
    ids=lambda p: p.name,
)
# params - num_rounds or env var ?
def test_downloads_one_object(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    """
    this test should use pytest-benchmark, 

    target_function should be `download_object`
    setup function should be `my_setup`
    no teardown function for now.
    
    """
    params, files_names = workload_params
    publish_benchmark_extra_info(benchmark, params)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = loop.run_until_complete(create_client())

    try:
        with monitor() as m:
            benchmark.pedantic(
                target=download_one_object_wrapper,
                iterations=1,
                rounds=params.rounds,
                args=(loop, client, files_names[0], params),
            )
    finally:
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
    object_size = params.file_size_bytes

    min_throughput = (object_size / (1024 * 1024)) / benchmark.stats["max"]
    max_throughput = (object_size / (1024 * 1024)) / benchmark.stats["min"]
    mean_throughput = (object_size / (1024 * 1024)) / benchmark.stats["mean"]
    median_throughput = (object_size / (1024 * 1024)) / benchmark.stats["median"]

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
    print("this is bucket -name ", params.bucket_name)
    print("this is filenames", files_names)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )
