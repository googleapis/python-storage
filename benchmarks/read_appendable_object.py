import argparse
import asyncio
import sys
import os
import threading
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)

async def get_persisted_size_async(bucket_name, object_name):
    """Opens an object and prints its persisted size."""
    # print(f"Getting persisted size for {object_name} in process {os.getpid()} and thread {threading.get_ident()}")
    client = AsyncGrpcClient().grpc_client
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()

    # one_gib = 1024 * 1024 * 1024
    # if mrd.persisted_size != one_gib:
    #     await mrd.close()
    #     raise ValueError(f"Object {object_name} has an unexpected size. Expected {one_gib}, but got {mrd.persisted_size}")
    # if random.randint(0, 100) % 5 == 0:
    print(f"Object: {object_name}, Persisted Size: {mrd.persisted_size}")
    # with open('b.txt','wb') as fp:
    #     await mrd.download_ranges([(0, mrd.persisted_size, fp)])

    await mrd.close()

def get_persisted_size_sync(bucket_name, object_name):
    """Wrapper to run the async get_persisted_size_async in a new event loop."""
    asyncio.run(get_persisted_size_async(bucket_name, object_name))

# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--bucket_name", type=str, default='chandrasiri-rs')
#     parser.add_argument("--count", type=int, default=100)
#     parser.add_argument("--start_object_num", type=int, default=0)
#     parser.add_argument("-n", "--num_workers", type=int, default=2)
#     parser.add_argument("--executor", type=str, choices=['thread', 'process'], default='process')
#     args = parser.parse_args()

#     ExecutorClass = ThreadPoolExecutor if args.executor == 'thread' else ProcessPoolExecutor

#     with ExecutorClass(max_workers=args.num_workers) as executor:
#         futures = []
#         for i in range(args.start_object_num, args.start_object_num + args.count):
#             object_name = f"py-sdk-mb-mt-{i}"
#             future = executor.submit(get_persisted_size_sync, args.bucket_name, object_name)
#             futures.append(future)

#         for future in futures:
#             future.result()

if __name__ == "__main__":
    get_persisted_size_sync(sys.argv[1], sys.argv[2])
