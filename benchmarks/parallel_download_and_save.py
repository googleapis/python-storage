
import argparse
import asyncio
from io import BytesIO
import multiprocessing
import os
import time
import threading
from google.cloud import storage
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)


async def download_range_async(
    client, bucket_name, object_name, start_byte, end_byte, chunk_size
):
    """
    Downloads a specific byte range of an object and returns the bytes.
    """
    download_size = end_byte - start_byte
    print(
        f"Downloading {object_name} from byte {start_byte} to {end_byte} (size {download_size}) in chunks of {chunk_size} from {bucket_name} from process {os.getpid()} and thread {threading.get_ident()}"
    )

    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()

    offset = 0
    output_buffer = BytesIO()
    while offset < download_size:
        bytes_to_download = min(chunk_size, download_size - offset)
        await mrd.download_ranges([(start_byte + offset, bytes_to_download, output_buffer)])
        offset += bytes_to_download

    assert (
        output_buffer.getbuffer().nbytes == download_size
    ), f"downloaded size incorrect for portion of {object_name}"

    await mrd.close()
    return (start_byte, output_buffer.getvalue())


async def run_coroutines(bucket_name, object_name, chunk_size, ranges):
    """
    Run coroutines for downloading specified ranges and return the downloaded chunks.
    """
    client = AsyncGrpcClient().grpc_client
    tasks = []
    for start, end in ranges:
        task = asyncio.create_task(
            download_range_async(
                client, bucket_name, object_name, start, end, chunk_size
            )
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results


def worker(bucket_name, object_name, chunk_size, ranges):
    """
    A worker process that downloads a set of byte ranges and returns the data.
    """
    print(f"Process {os.getpid()} starting with {len(ranges)} ranges.")
    downloaded_chunks = asyncio.run(run_coroutines(bucket_name, object_name, chunk_size, ranges))
    return downloaded_chunks


def main():
    parser = argparse.ArgumentParser(
        description="Download a GCS object in parallel and save it to a file."
    )
    parser.add_argument("--bucket_name", type=str, default="chandrasiri-rs", help="GCS bucket name.")
    parser.add_argument("--object_name", type=str, required=True, help="GCS object name.")
    parser.add_argument("--output_file", type=str, required=True, help="Path to save the downloaded file.")
    parser.add_argument("--size", type=int, default=1024**3, help="Object size.")
    parser.add_argument("-n", "--num_processes", type=int, default=4, help="Number of processes to use.")
    parser.add_argument("-m", "--num_coroutines_per_process", type=int, default=2, help="Number of coroutines per process.")
    parser.add_argument("--chunk_size", type=int, default=64 * 1024 * 1024, help="Chunk size for each download stream.")

    args = parser.parse_args()

    # Get object size from args
    object_size = args.size

    total_coroutines = args.num_processes * args.num_coroutines_per_process
    
    print(f"Starting download of {args.object_name} ({object_size} bytes) from bucket {args.bucket_name}")
    print(f"Using {args.num_processes} processes and {args.num_coroutines_per_process} coroutines per process ({total_coroutines} total workers).")

    # Calculate ranges
    base_range_size = object_size // total_coroutines
    remainder = object_size % total_coroutines
    
    ranges = []
    current_byte = 0
    for i in range(total_coroutines):
        range_size = base_range_size + (1 if i < remainder else 0)
        start_byte = current_byte
        end_byte = current_byte + range_size
        ranges.append((start_byte, end_byte))
        current_byte = end_byte

    # Distribute adjacent ranges among processes
    ranges_per_process = args.num_coroutines_per_process
    process_ranges = [
        ranges[i * ranges_per_process : (i + 1) * ranges_per_process]
        for i in range(args.num_processes)
    ]

    start_time = time.perf_counter()

    with multiprocessing.Pool(args.num_processes) as pool:
        results = pool.starmap(worker, [(args.bucket_name, args.object_name, args.chunk_size, pr) for pr in process_ranges])

    # Flatten the list of lists, sort by start_byte, and write to file
    all_chunks = [chunk for process_result in results for chunk in process_result]
    all_chunks.sort(key=lambda x: x[0])

    total_downloaded_bytes = 0
    with open(args.output_file, "wb") as f:
        for start_byte, data in all_chunks:
            f.write(data)
            total_downloaded_bytes += len(data)

    end_time = time.perf_counter()

    print("\n--- Download Complete ---")
    print(f"File saved to: {args.output_file}")
    print(f"Total downloaded bytes: {total_downloaded_bytes}")
    assert total_downloaded_bytes == object_size, "Mismatch in downloaded size"

    duration = end_time - start_time
    throughput = total_downloaded_bytes / duration / (1024 * 1024)  # MB/s

    print(f"Total time: {duration:.2f} seconds")
    print(f"Throughput: {throughput:.2f} MB/s")


if __name__ == "__main__":
    main()
