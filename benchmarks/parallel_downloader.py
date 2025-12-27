import asyncio
import multiprocessing
import os
import time
from io import BytesIO
from multiprocessing import Pool

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)


async def download_object_async(bucket_name, object_name):
    """Downloads a single object and saves it to a local file."""
    client = AsyncGrpcClient().grpc_client
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()
    buffer = BytesIO()
    await mrd.download_ranges(read_ranges=[(0, 0, buffer)])
    await mrd.close()

    assert buffer.getbuffer().nbytes == 100 * 1024 * 1024  # 100 MiB

    # Save the downloaded object to a local file
    # with open(object_name, "wb") as f:
    #     f.write(buffer.getvalue())

    print(f"Finished downloading {object_name}")


def download_worker(object_name):
    """A synchronous wrapper to be called by multiprocessing."""
    bucket_name = "chandrasiri-rs"
    try:
        asyncio.run(download_object_async(bucket_name, object_name))
        return f"Successfully downloaded {object_name}"
    except Exception as e:
        print(f"Failed to download {object_name}: {e}")
        raise


def main():
    """Main function to orchestrate parallel downloads."""
    num_objects = 3000
    num_processes = 64

    object_names = [f"para_64-{i}" for i in range(num_objects)]

    # Ensure the directory for downloaded files exists
    # This example saves to the current working directory.
    # For large numbers of files, consider a dedicated directory.
    start_time = time.monotonic_ns()
    with Pool(processes=num_processes) as pool:
        for result in pool.imap_unordered(download_worker, object_names):
            print(result)
    end_time = time.monotonic_ns()

    print(
        f"\nFinished all download attempts for {num_objects} objects: took - {end_time - start_time / 10**9}s"
    )


if __name__ == "__main__":
    # Using 'fork' as the start method is recommended for compatibility
    # with asyncio in a multiprocessing context.
    multiprocessing.set_start_method("fork", force=True)
    main()
