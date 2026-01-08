import asyncio
import multiprocessing
import os
from multiprocessing import Pool

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)


async def upload_object_async(bucket_name, object_name):
    """Uploads a single object with 100MiB of random data."""
    num_bytes_to_append = 100 * 1024 * 1024  # 100 MiB
    data = os.urandom(num_bytes_to_append)

    client = AsyncGrpcClient().grpc_client
    writer = AsyncAppendableObjectWriter(
        client=client, bucket_name=bucket_name, object_name=object_name
    )

    await writer.open()
    await writer.append(data)
    # await writer.flush()
    await writer.close()
    print(f"Finished uploading {object_name}")


def upload_worker(object_name):
    """A synchronous wrapper to be called by multiprocessing."""
    bucket_name = "chandrasiri-benchmarks-zb"  # Replace with your bucket name
    try:
        asyncio.run(upload_object_async(bucket_name, object_name))
        return f"Successfully uploaded {object_name}"
    except Exception as e:
        print(f"Failed to upload {object_name}: {e}")
        raise


def main():
    """Main function to orchestrate parallel uploads."""
    num_objects = 3000
    num_processes = 64

    object_names = [f"high_mem_long_running-{i}" for i in range(num_objects)]

    with Pool(processes=num_processes) as pool:
        for result in pool.imap_unordered(upload_worker, object_names):
            print(result)

    print(f"\nFinished all upload attempts for {num_objects} objects.")


if __name__ == "__main__":
    # Using 'fork' as the start method is recommended for compatibility
    # with asyncio in a multiprocessing context.
    multiprocessing.set_start_method("fork", force=True)
    main()
