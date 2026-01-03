import argparse
import asyncio
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
import math
import uuid

async def upload_one_async(bucket_name, object_name, upload_size, chunk_size):
    """Uploads a single object of size `upload_size`, in chunks of `chunk_size`"""
    print(f"Uploading {object_name} of size {upload_size} in chunks of {chunk_size} to {bucket_name} from process {os.getpid()} and thread {threading.get_ident()}")
    client = AsyncGrpcClient().grpc_client
    start_time = time.perf_counter()
    writer = AsyncAppendableObjectWriter(
        client=client, bucket_name=bucket_name, object_name=object_name
    )

    await writer.open()
    uploaded_bytes = 0
    count = 0
    while uploaded_bytes < upload_size:
        bytes_to_upload = min(chunk_size, upload_size - uploaded_bytes)
        data = os.urandom(bytes_to_upload)
        await writer.append(data)
        uploaded_bytes += bytes_to_upload
        count += 1
    await writer.close()
    assert uploaded_bytes == upload_size
    assert count == math.ceil(upload_size / chunk_size)

    end_time = time.perf_counter()
    latency = end_time - start_time
    throughput = (upload_size / latency) / (1000 * 1000)  # MB/s

    print(f"Finished uploading {object_name}")
    print(f"Latency: {latency:.2f} seconds")
    print(f"Throughput: {throughput:.2f} MB/s")

# def upload_one_sync(bucket_name, object_name, upload_size, chunk_size):
#     """Wrapper to run the async upload_one in a new event loop."""
#     asyncio.run(upload_one_async(bucket_name, object_name, upload_size, chunk_size))


# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--bucket_name", type=str, default='chandrasiri-rs')
#     parser.add_argument("--upload_size", type=int, default=1024 * 1024 * 1024)  # 1 GiB
#     parser.add_argument("--chunk_size", type=int, default=100 * 1024 * 1024)  # 100 MiB
#     parser.add_argument("--count", type=int, default=100)
#     parser.add_argument("--start_object_num", type=int, default=0)
#     parser.add_argument("-n", "--num_workers", type=int, default=2, help="Number of worker threads or processes.")
#     parser.add_argument("--executor", type=str, choices=['thread', 'process'], default='process', help="Executor to use: 'thread' for ThreadPoolExecutor, 'process' for ProcessPoolExecutor")
#     args = parser.parse_args()

#     total_start_time = time.perf_counter()

#     ExecutorClass = ThreadPoolExecutor if args.executor == 'thread' else ProcessPoolExecutor

#     with ExecutorClass(max_workers=args.num_workers) as executor:
#         futures = []
#         for i in range(args.start_object_num, args.start_object_num + args.count):
#             object_name = f"py-sdk-mb-mt-{i}"
#             future = executor.submit(upload_one_sync, args.bucket_name, object_name, args.upload_size, args.chunk_size)
#             futures.append(future)

#         for future in futures:
#             future.result() # wait for all workers to complete

#     total_end_time = time.perf_counter()
#     total_latency = total_end_time - total_start_time
#     total_uploaded_bytes = args.upload_size * args.count
#     aggregate_throughput = (total_uploaded_bytes / total_latency) / (1000 * 1000)  # MB/s

#     print("\n--- Aggregate Results ---")
#     print(f"Total objects uploaded: {args.count}")
#     print(f"Total data uploaded: {total_uploaded_bytes / (1024*1024*1024):.2f} GiB")
#     print(f"Total time taken: {total_latency:.2f} seconds")
#     print(f"Aggregate throughput: {aggregate_throughput:.2f} MB/s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, default='chandrasiri-rs')
    # parser.add_argument("--object_suffix", type=str, required=True)
    parser.add_argument("--upload_size", type=int, default=1024 * 1024 * 1024)  # 1 GiB
    parser.add_argument("--chunk_size", type=int, default=100 * 1024 * 1024)  # 100 MiB
    args = parser.parse_args()
    object_name = f'upload-test-{str(uuid.uuid4())[:4]}'
    asyncio.run(upload_one_async(args.bucket_name, object_name, args.upload_size, args.chunk_size))
