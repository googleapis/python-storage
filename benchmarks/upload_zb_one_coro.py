import argparse
import asyncio
import os
import time

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
import logging
import sys


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

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
    throughput = (upload_size / latency) / (10**6)  # MB/s

    print(f"Finished uploading {object_name}, with generation, {writer.generation}")
    print(f"Latency: {latency:.2f} seconds")
    print(f"Throughput: {throughput:.2f} MB/s")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, default='chandrasiri-rs')
    parser.add_argument("--upload_size", type=int, default=1024 * 1024 * 1024)  # 100 MiB
    parser.add_argument("--chunk_size", type=int, default=100 * 1024 * 1024)  # 10 MiB
    args = parser.parse_args()

    client = AsyncGrpcClient().grpc_client
    # object_name = f"test-half-close-current-code" # generation 1767887565143753
    # object_name = f"test-half-close-with-good-close"
    object_name = f"test-logs"

    await upload_one(client, args.bucket_name, object_name, args.upload_size, args.chunk_size)

if __name__ == "__main__":
    asyncio.run(main(), debug=True)