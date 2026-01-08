import argparse
import asyncio
from io import BytesIO
import os
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)

async def download_one_async(bucket_name, object_name, download_size, chunk_size):
    """Downloads a single object of size `download_size`, in chunks of `chunk_size`"""
    print(f"Downloading {object_name} of size {download_size} in chunks of {chunk_size} from {bucket_name} from process {os.getpid()} and thread {threading.get_ident()}")
    # raise NotImplementedError("This function is not yet implemented.")
    client = AsyncGrpcClient().grpc_client

    # log_peak_memory_usage()
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()
    
    # download in chunks of `chunk_size`
    offset = 0
    output_buffer = BytesIO()
    while offset < download_size:
        bytes_to_download = min(chunk_size, download_size - offset)    
        await mrd.download_ranges([(offset, bytes_to_download, output_buffer)])
        offset += bytes_to_download
    # await mrd.download_ranges([(offset, 0, output_buffer)])
    assert output_buffer.getbuffer().nbytes == download_size, f"downloaded size incorrect for {object_name}"
    
    await mrd.close()

def download_one_sync(bucket_name, object_name, download_size, chunk_size):
    """Wrapper to run the async download_one in a new event loop."""
    asyncio.run(download_one_async(bucket_name, object_name, download_size, chunk_size))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, default='chandrasiri-rs')
    parser.add_argument("--download_size", type=int, default=1024 * 1024 * 1024)  # 1 GiB
    parser.add_argument("--chunk_size", type=int, default=64 * 1024 * 1024)  # 100 MiB
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--start_object_num", type=int, default=0)
    parser.add_argument("-n", "--num_workers", type=int, default=2, help="Number of worker threads or processes.")
    parser.add_argument("--executor", type=str, choices=['thread', 'process'], default='process', help="Executor to use: 'thread' for ThreadPoolExecutor, 'process' for ProcessPoolExecutor")
    args = parser.parse_args()

    total_start_time = time.perf_counter()

    ExecutorClass = ThreadPoolExecutor if args.executor == 'thread' else ProcessPoolExecutor
    object_count = args.count
    with ExecutorClass(max_workers=args.num_workers) as executor:
        futures = []
        for i in range(args.start_object_num, args.start_object_num + object_count):
            object_name = f"py-sdk-mb-mt-{i}"
            future = executor.submit(download_one_sync, args.bucket_name, object_name, args.download_size, args.chunk_size)
            futures.append(future)
        
        for future in futures:
            future.result() # wait for all workers to complete and raise exceptions

    total_end_time = time.perf_counter()
    total_latency = total_end_time - total_start_time
    total_downloaded_bytes = args.download_size * object_count
    aggregate_throughput = (total_downloaded_bytes / total_latency) / (1000 * 1000)  # MB/s

    print("\n--- Aggregate Results ---")
    print(f"Total objects to download: {object_count}")
    print(f"Total data to download: {total_downloaded_bytes / (1024*1024*1024):.2f} GiB")
    print(f"Total time taken: {total_latency:.2f} seconds")
    print(f"Aggregate throughput: {aggregate_throughput:.2f} MB/s")


if __name__ == "__main__":
    main()
