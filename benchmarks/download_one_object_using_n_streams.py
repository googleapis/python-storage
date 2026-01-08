import argparse
import asyncio
from io import BytesIO
import os
import time
import threading

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)


async def download_range_async(
    client, bucket_name, object_name, start_byte, end_byte, chunk_size
):
    """
    Downloads a specific byte range of an object.
    This is a modified version of the original download_one_async, adapted to
    download a portion of an object.
    """
    download_size = end_byte - start_byte
    print(
        f"Downloading {object_name} from byte {start_byte} to {end_byte} (size {download_size}) in chunks of {chunk_size} from {bucket_name} from process {os.getpid()} and thread {threading.get_ident()}"
    )

    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()

    offset = 0
    output_buffer = BytesIO()

    start_time = time.perf_counter()
    while offset < download_size:
        bytes_to_download = min(chunk_size, download_size - offset)
        await mrd.download_ranges(
            [(start_byte + offset, bytes_to_download, output_buffer)]
        )
        offset += bytes_to_download
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    throughput_mbs = (
        (download_size / elapsed_time) / (1000 * 1000) if elapsed_time > 0 else 0
    )

    print(f"Time taken for download loop: {elapsed_time:.4f} seconds")
    print(f"Throughput for this range: {throughput_mbs:.2f} MB/s")

    assert (
        output_buffer.getbuffer().nbytes == download_size
    ), f"downloaded size incorrect for portion of {object_name}"

    await mrd.close()
    return output_buffer


async def download_one_object_with_n_streams_async(
    bucket_name, object_name, download_size, chunk_size, num_streams
):
    """
    Downloads a single object using 'n' concurrent streams.
    It divides the object into 'n' parts and creates an async task to download each part.
    """
    print(
        f"Downloading {object_name} of size {download_size} from {bucket_name} using {num_streams} streams."
    )

    # Create one client to be shared by all download tasks.
    client = AsyncGrpcClient().grpc_client

    tasks = []

    # Calculate the byte range for each stream.
    portion_size = download_size // num_streams

    for i in range(num_streams):
        start = i * portion_size
        end = start + portion_size
        if i == num_streams - 1:
            # The last stream downloads any remaining bytes.
            end = download_size

        task = asyncio.create_task(
            download_range_async(
                client, bucket_name, object_name, start, end, chunk_size
            )
        )
        tasks.append(task)

    # Wait for all download tasks to complete.
    downloaded_parts = await asyncio.gather(*tasks)

    # Stitch the downloaded parts together in the correct order.
    final_buffer = BytesIO()
    for part in downloaded_parts:
        final_buffer.write(part.getbuffer())

    # Verify the final size.
    final_size = final_buffer.getbuffer().nbytes
    assert (
        final_size == download_size
    ), f"Downloaded size incorrect for {object_name}. Expected {download_size}, got {final_size}"
    print(f"Successfully downloaded {object_name} with size {final_size}")


def main():
    parser = argparse.ArgumentParser(
        description="Download a single GCS object using multiple concurrent streams."
    )
    parser.add_argument("--bucket_name", type=str, default="chandrasiri-rs")
    parser.add_argument(
        "--download_size", type=int, default=1024 * 1024 * 1024
    )  # 1 GiB
    parser.add_argument(
        "--chunk_size", type=int, default=64 * 1024 * 1024
    )  # 64 MiB
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of times to run the download (for benchmarking).",
    )
    parser.add_argument(
        "--start_object_num",
        type=int,
        default=0,
        help="The number of the object to download (e.g., py-sdk-mb-mt-{start_object_num}).",
    )
    parser.add_argument(
        "-n",
        "--num_workers",
        type=int,
        default=10,
        help="Number of streams to use for downloading.",
    )
    args = parser.parse_args()

    total_start_time = time.perf_counter()

    object_name = f"py-sdk-mb-mt-{args.start_object_num}"

    for i in range(args.count):
        print(f"\n--- Starting download run {i+1}/{args.count} ---")
        run_start_time = time.perf_counter()

        asyncio.run(
            download_one_object_with_n_streams_async(
                args.bucket_name,
                object_name,
                args.download_size,
                args.chunk_size,
                args.num_workers,
            )
        )

        run_end_time = time.perf_counter()
        run_latency = run_end_time - run_start_time
        run_throughput = (args.download_size / run_latency) / (1000 * 1000)
        print(f"Run {i+1} throughput: {run_throughput:.2f} MB/s")

    total_end_time = time.perf_counter()
    total_latency = total_end_time - total_start_time
    total_downloaded_bytes = args.download_size * args.count
    aggregate_throughput = (total_downloaded_bytes / total_latency) / (
        1000 * 1000
    )  # MB/s

    print("\n--- Aggregate Results ---")
    print(f"Total download runs: {args.count}")
    print(f"Object name: {object_name}")
    print(
        f"Total data downloaded: {total_downloaded_bytes / (1024*1024*1024):.2f} GiB"
    )
    print(f"Total time taken: {total_latency:.2f} seconds")
    print(f"Aggregate throughput: {aggregate_throughput:.2f} MB/s")
    print(f"Number of streams used per download: {args.num_workers}")


if __name__ == "__main__":
    main()
