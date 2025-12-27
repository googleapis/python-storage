import argparse
import asyncio
import os
import time

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)

async def upload_one(client, bucket_name, object_name, upload_size, chunk_size):
    """Uploads a single object of size `upload_size`, in chunks of `chunk_size`"""
    print(f"Uploading {object_name} of size {upload_size} in chunks of {chunk_size} to {bucket_name}")

    writer = AsyncAppendableObjectWriter(
        client=client, bucket_name=bucket_name, object_name=object_name
    )

    await writer.open()
    
    start_time = time.perf_counter()
    
    uploaded_bytes = 0
    while uploaded_bytes < upload_size:
        bytes_to_upload = min(chunk_size, upload_size - uploaded_bytes)
        data = os.urandom(bytes_to_upload)
        await writer.append(data)
        uploaded_bytes += bytes_to_upload
    
    await writer.close()
    
    end_time = time.perf_counter()
    latency = end_time - start_time
    throughput = (upload_size / latency) / (1000 * 1000)  # MB/s

    print(f"Finished uploading {object_name}")
    print(f"Latency: {latency:.2f} seconds")
    print(f"Throughput: {throughput:.2f} MB/s")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, default='chandrasiri-rs')
    parser.add_argument("--upload_size", type=int, default=1024 * 1024 * 1024)  # 1 GiB
    parser.add_argument("--chunk_size", type=int, default=100 * 1024 * 1024)  # 100 MiB
    parser.add_argument("-n", "--num_coros", type=int, default=2)
    args = parser.parse_args()

    client = AsyncGrpcClient().grpc_client
    
    total_start_time = time.perf_counter()

    tasks = []
    for i in range(args.num_coros):
        object_name = f"py-sdk-mb-mc-{i}"
        task = upload_one(client, args.bucket_name, object_name, args.upload_size, args.chunk_size)
        tasks.append(task)
    
    await asyncio.gather(*tasks)

    total_end_time = time.perf_counter()
    total_latency = total_end_time - total_start_time
    total_uploaded_bytes = args.upload_size * args.num_coros
    aggregate_throughput = (total_uploaded_bytes / total_latency) / (1000 * 1000)  # MB/s

    print("\n--- Aggregate Results ---")
    print(f"Total objects uploaded: {args.num_coros}")
    print(f"Total data uploaded: {total_uploaded_bytes / (1024*1024*1024):.2f} GiB")
    print(f"Total time taken: {total_latency:.2f} seconds")
    print(f"Aggregate throughput: {aggregate_throughput:.2f} MB/s")


if __name__ == "__main__":
    asyncio.run(main())