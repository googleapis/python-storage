#!/usr/bin/env python

# Copyright 2026 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import asyncio
import time
import statistics
from io import BytesIO

from google.cloud.storage.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
import random

OBJECT_SIZE = 1024**3  # 1 GiB


async def benchmark_single_stream(bucket_name, object_name, num_ranges, range_size):
    """Benchmark downloading n ranges using 1 stream."""
    grpc_client = AsyncGrpcClient()
    mrd = AsyncMultiRangeDownloader(grpc_client, bucket_name, object_name)

    total_downloaded_size = 0
    start_time = time.monotonic()
    try:
        await mrd.open()

        buffers = [BytesIO() for _ in range(num_ranges)]
        # ranges = [(i * range_size, range_size, buffers[i]) for i in range(num_ranges)]
        ranges = []
        for i in range(num_ranges):
            offset = random.randint(0, OBJECT_SIZE - range_size)
            ranges.append((offset, range_size, buffers[i]))

        # start_time = time.monotonic()
        await mrd.download_ranges(ranges)
        end_time = time.monotonic()

        for output_buffer in buffers:
            total_downloaded_size += output_buffer.getbuffer().nbytes

    finally:
        await mrd.close()

    latency = end_time - start_time
    throughput = total_downloaded_size / (1024 * 1024) / latency
    # print(f"Total downloaded size: {total_downloaded_size} bytes")
    # print(f"Time taken: {latency:.4f} seconds")
    # print(f"Throughput: {throughput:.4f} MiB/s")
    return latency, throughput


async def download_one_range(mrd, start_byte, range_size, buffer):
    """Helper coroutine for multi-stream benchmark"""
    await mrd.download_ranges([(start_byte, range_size, buffer)])


async def benchmark_multi_stream(
    bucket_name, object_name, num_ranges, range_size, num_workers
):
    """Benchmark downloading n ranges in n streams."""
    grpc_client = AsyncGrpcClient()
    buffers = [BytesIO() for _ in range(num_ranges)]
    mrds = [
        AsyncMultiRangeDownloader(grpc_client, bucket_name, object_name)
        for _ in range(num_ranges)
    ]

    total_downloaded_size = 0
    start_time = time.monotonic()
    try:
        await asyncio.gather(*(mrd.open() for mrd in mrds))

        tasks = []
        for i in range(num_ranges):
            offset = random.randint(0, OBJECT_SIZE - range_size)
            task = asyncio.create_task(
                download_one_range(
                    mrds[i],
                    offset,
                    range_size,
                    buffers[i],
                )
            )
            tasks.append(task)

        # start_time = time.monotonic()
        await asyncio.gather(*tasks)
        end_time = time.monotonic()

        for output_buffer in buffers:
            total_downloaded_size += output_buffer.getbuffer().nbytes
    finally:
        await asyncio.gather(*(mrd.close() for mrd in mrds))

    latency = end_time - start_time
    throughput = total_downloaded_size / (1024 * 1024) / latency
    # print(f"Total downloaded size: {total_downloaded_size} bytes")
    # print(f"Time taken: {latency:.4f} seconds")
    # print(f"Throughput: {throughput:.4f} MiB/s")
    return latency, throughput


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--bucket_name", help="Your Cloud Storage bucket name.", required=True
    )
    parser.add_argument(
        "--object_name", help="Your Cloud Storage object name.", required=True
    )
    parser.add_argument(
        "--num_ranges", help="Number of ranges to download.", type=int, default=10
    )
    parser.add_argument(
        "--range_size",
        help="Size of each range in bytes.",
        type=int,
        default=1024 * 1024,
    )
    parser.add_argument(
        "--num_workers",
        help="Number of concurrent workers for multi-stream download.",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--num_iterations",
        help="Number of iterations to run the benchmark.",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--scenario",
        choices=["single-stream", "multi-stream", "all"],
        default="all",
        help="Which benchmark scenario to run.",
    )

    args = parser.parse_args()

    if args.scenario == "single-stream" or args.scenario == "all":
        latencies = []
        throughputs = []
        for i in range(args.num_iterations):
            # print(f"\n--- Running single-stream iteration {i+1}/{args.num_iterations} ---")
            latency, throughput = asyncio.run(
                benchmark_single_stream(
                    args.bucket_name, args.object_name, args.num_ranges, args.range_size
                )
            )
            latencies.append(latency)
            throughputs.append(throughput)

        print("\n--- single-stream Benchmark Summary ---")
        if latencies:
            print(f"Latencies (s):")
            print(f"  Mean: {statistics.mean(latencies):.4f}")
            print(f"  Median: {statistics.median(latencies):.4f}")
            print(f"  Min: {min(latencies):.4f}")
            print(f"  Max: {max(latencies):.4f}")

        if throughputs:
            print(f"Throughputs (MiB/s):")
            print(f"  Mean: {statistics.mean(throughputs):.4f}")
            print(f"  Median: {statistics.median(throughputs):.4f}")
            print(f"  Min: {min(throughputs):.4f}")
            print(f"  Max: {max(throughputs):.4f}")

    if args.scenario == "multi-stream" or args.scenario == "all":
        latencies = []
        throughputs = []
        for i in range(args.num_iterations):
            # print(f"\n--- Running multi-stream iteration {i+1}/{args.num_iterations} ---")
            latency, throughput = asyncio.run(
                benchmark_multi_stream(
                    args.bucket_name,
                    args.object_name,
                    args.num_ranges,
                    args.range_size,
                    args.num_workers,
                )
            )
            latencies.append(latency)
            throughputs.append(throughput)

        print("\n--- multi-stream Benchmark Summary ---")
        if latencies:
            print(f"Latencies (s):")
            print(f"  Mean: {statistics.mean(latencies):.4f}")
            print(f"  Median: {statistics.median(latencies):.4f}")
            print(f"  Min: {min(latencies):.4f}")
            print(f"  Max: {max(latencies):.4f}")

        if throughputs:
            print(f"Throughputs (MiB/s):")
            print(f"  Mean: {statistics.mean(throughputs):.4f}")
            print(f"  Median: {statistics.median(throughputs):.4f}")
            print(f"  Min: {min(throughputs):.4f}")
            print(f"  Max: {max(throughputs):.4f}")
