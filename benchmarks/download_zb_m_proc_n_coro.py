import argparse
import asyncio
from datetime import datetime, timedelta
from io import BytesIO
import os
import time
import threading
import logging
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tests.perf.microbenchmarks.resource_monitor import ResourceMonitor

async def download_one_async(bucket_name, object_name, download_size, chunk_size):
    """Downloads a single object of size `download_size`, in chunks of `chunk_size`"""
    logging.debug(f"Downloading {object_name} of size {download_size} in chunks of {chunk_size} from {bucket_name} from process {os.getpid()} and thread {threading.get_ident()}")
    client = AsyncGrpcClient().grpc_client

    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    
    start_time = time.perf_counter()
    await mrd.open()
    
    offset = 0
    output_buffer = BytesIO()
    while offset < download_size:
        bytes_to_download = min(chunk_size, download_size - offset)    
        await mrd.download_ranges([(offset, bytes_to_download, output_buffer)])
        offset += bytes_to_download

    assert output_buffer.getbuffer().nbytes == download_size, f"downloaded size incorrect for {object_name}"
    
    await mrd.close()
    end_time = time.perf_counter()
    return end_time - start_time

def run_coroutines(bucket_name, object_names, download_size, chunk_size):
    """Runs a number of coroutines to download objects concurrently and returns their latencies."""
    async def main():
        tasks = [
            download_one_async(bucket_name, object_name, download_size, chunk_size)
            for object_name in object_names
        ]
        return await asyncio.gather(*tasks)
    
    return asyncio.run(main())

def main():
    multiprocessing.set_start_method("spawn")
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, default='chandrasiri-rs')
    parser.add_argument("--download_size_mib", type=int, default=1024)  # 1 GiB
    parser.add_argument("--chunk_size_mib", type=int, default=64)  # 100 MiB
    parser.add_argument("--count", type=int, default=4, help="The total number of objects to download.")
    parser.add_argument("-m", "--num_processes", type=int, default=2, help="Number of worker processes.")
    parser.add_argument("-n", "--num_coros", type=int, default=2, help="Number of worker coroutines.")
    parser.add_argument("--start_object_num", type=int, default=0)
    parser.add_argument(
        "--run_for_minutes",
        type=int,
        default=0,
        help="Number of minutes to run this process. If not provided, it runs for 1 iteration.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

    iteration = 0
    start_time = datetime.now()

    def should_run():
        if args.run_for_minutes > 0:
            return datetime.now() - start_time < timedelta(minutes=args.run_for_minutes)
        else:
            return iteration == 0

    while should_run():
        logging.info(f"\n--- Iteration {iteration + 1} ---")
        iteration += 1
        total_start_time = time.perf_counter()

        total_objects = args.count
        all_object_names = [f"py-sdk-mb-mt-{i}" for i in range(args.start_object_num, args.start_object_num + total_objects)]

        all_latencies = []
        m = ResourceMonitor()

        with m, ProcessPoolExecutor(max_workers=args.num_processes) as executor:
            futures = []
            for i in range(0, len(all_object_names), args.num_coros):
                objects = all_object_names[i:i + args.num_coros]
                future = executor.submit(
                    run_coroutines, args.bucket_name, objects, args.download_size_mib * 1024 * 1024, args.chunk_size_mib * 1024 * 1024
                )
                futures.append(future)

            
        for future in futures:
            all_latencies.extend(future.result())

        total_end_time = time.perf_counter()
        total_time_taken = total_end_time - total_start_time
        total_downloaded_bytes = args.download_size_mib * 1024 * 1024 * total_objects
        # m.throughput_mb_s = (total_downloaded_bytes / (1024*1024)) / total_time_taken if total_time_taken else 0

        # Calculate throughput per-download and get the average

        average_throughput = total_downloaded_bytes / total_time_taken / (1024 * 1024)  # MiB/s
        logging.info("\n--- Aggregate Results ---")
        logging.info(f"Total objects to download: {total_objects}")
        logging.info(f"Total data to download: {total_downloaded_bytes / (1024*1024*1024):.2f} GiB")
        logging.info(f"Total time taken: {total_time_taken:.2f} seconds")
        logging.info(f"Average throughput: {average_throughput:.2f} MB/s")

        logging.info("\n--- Resource Monitor Results ---")
        logging.info(f"Max CPU: {m.max_cpu}")
        logging.info(f"Max Memory: {m.max_mem}")
        logging.info(f"Throughput (MB/s): {m.throughput_mb_s}")
        logging.info(f"vCPUs: {m.vcpus}")

if __name__ == "__main__":
    main()