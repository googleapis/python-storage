import argparse
import asyncio
import os
import time

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
from google.cloud import storage



def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket using the standard synchronous client."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        print(f"--- Deleting blob {blob_name} from bucket {bucket_name}. ---", flush=True)
        blob.delete()
        print(f"--- Blob {blob_name} deleted. ---", flush=True)
    except Exception as e:
        print(f"--- Error deleting blob {blob_name}: {e} ---", flush=True)


async def upload_one(client, bucket_name, object_name, upload_size, chunk_size):
    """Uploads a single object of size `upload_size`, in chunks of `chunk_size`"""
    print(
        f"Uploading {object_name} of size {upload_size / (1024**3):.0f} GiB in chunks of {chunk_size / (1024**3):.0f} GiB to {bucket_name}",
        flush=True
    )

    writer = AsyncAppendableObjectWriter(
        client=client, bucket_name=bucket_name, object_name=object_name, writer_options={"FLUSH_INTERVAL_BYTES": chunk_size}
    )

    await writer.open()

    start_time = time.perf_counter()

    # Using a pre-allocated buffer for performance instead of os.urandom.
    chunk = os.urandom(chunk_size)
    uploaded_bytes = 0
    while uploaded_bytes < upload_size:
        # In a real-world scenario, you would read data from a source here.
        # For this benchmark, we just send the same chunk repeatedly.
        bytes_to_upload = min(chunk_size, upload_size - uploaded_bytes)
        await writer.append(chunk[:bytes_to_upload])
        uploaded_bytes += bytes_to_upload

    response = await writer.close(finalize_on_close=True)
    print(f"Upload response for {object_name}: {response}", flush=True)

    end_time = time.perf_counter()
    latency = end_time - start_time
    throughput = (upload_size / latency) / (10**6)  # MB/s

    print(f"Finished uploading {object_name}", flush=True)
    print(f"Latency: {latency:.2f} seconds", flush=True)
    print(f"Throughput: {throughput:.2f} MB/s", flush=True)


async def main():
    parser = argparse.ArgumentParser(
        description="Benchmark large object uploads and deletions."
    )
    parser.add_argument(
        "--bucket_name",
        type=str,
        default="chandrasiri-benchmarks-zb",
        help="The GCS bucket to upload to.",
    )
    args = parser.parse_args()

    async_client = AsyncGrpcClient().grpc_client
    chunk_size_bytes = 1 * 1024 * 1024 * 1024  # 1 GiB

    # Loop from 100 GiB to 1 TiB (1024 GiB) in 100 GiB increments.
    for i in range(2, 5):
        size_gib = i*100
        upload_size_bytes = size_gib * 1024 * 1024 * 1024
        object_name = f"large-upload-benchmark-{size_gib}gib"

        print("\n" + "=" * 60, flush=True)
        print(f"Starting Test Case: {size_gib} GiB Object Upload", flush=True)
        print("=" * 60 + "\n", flush=True)

        try:
            await upload_one(
                async_client,
                args.bucket_name,
                object_name,
                upload_size_bytes,
                chunk_size_bytes,
            )
        except Exception as e:
            print(f"An error occurred during the upload for {object_name}: {e}", flush=True)
        finally:
            # Ensure the object is deleted after the test, even if the upload failed.
            # We run the synchronous delete function in a separate thread to avoid
            # blocking the asyncio event loop.
            await asyncio.to_thread(delete_blob, args.bucket_name, object_name)


if __name__ == "__main__":
    asyncio.run(main())