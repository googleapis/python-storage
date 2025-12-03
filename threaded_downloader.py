import asyncio
import time
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)


async def download_object_async(bucket_name, object_name):
    """Downloads a single object."""
    client = AsyncGrpcClient().grpc_client
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()
    buffer = BytesIO()
    await mrd.download_ranges(read_ranges=[(0, 0, buffer)])
    await mrd.close()

    assert buffer.getbuffer().nbytes == 100 * 1024 * 1024  # 100 MiB

    # Save the downloaded object to a local file
    with open(object_name, "wb") as f:
        f.write(buffer.getvalue())

    print(f"Finished downloading {object_name}")


def download_worker(object_name):
    """A synchronous wrapper to be called by a thread."""
    bucket_name = "chandrasiri-rs"
    try:
        # asyncio.run() creates a new event loop for each thread.
        asyncio.run(download_object_async(bucket_name, object_name))
        return f"Successfully downloaded {object_name}"
    except Exception as e:
        # Log the error and return a failure message so other downloads can continue.
        error_message = f"Failed to download {object_name}: {e}"
        print(error_message)
        return error_message


def main():
    """Main function to orchestrate parallel downloads using threads."""
    num_objects = 6
    num_threads = 1

    object_names = [f"para_64-{i}" for i in range(num_objects)]

    print(f"Starting download of {num_objects} objects using {num_threads} threads...")
    start_time = time.monotonic()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # executor.map runs the worker function for each item in object_names
        # and returns results as they are completed.
        results = executor.map(download_worker, object_names)
        for result in results:
            # The result is printed here, but it could also be collected
            # for a summary at the end.
            pass  # The worker already prints success or failure.

    end_time = time.monotonic()

    print(
        f"\nFinished all download attempts for {num_objects} objects. Total time: {end_time - start_time:.2f}s"
    )


if __name__ == "__main__":
    main()
