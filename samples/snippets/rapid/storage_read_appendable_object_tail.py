#!/usr/bin/env python

# Copyright 2026 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import asyncio
import time
from datetime import datetime
from io import BytesIO

from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
import os


# [START storage_read_appendable_object_tail]
async def appender(writer: AsyncAppendableObjectWriter, duration: int):
    """Appends 10 bytes to the object every second for a given duration."""
    print("Appender started.")
    for i in range(duration):
        await writer.append(os.urandom(10))  # Append 10 random bytes.
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{now}] Appended 1 byte. Total appended: {i + 1}")
        await asyncio.sleep(1)
    print("Appender finished.")


async def tailer(bucket_name: str, object_name: str, duration: int):
    """Tails the object by reading new data as it is appended."""
    print("Tailer started.")
    start_byte = 0
    client = AsyncGrpcClient().grpc_client
    start_time = time.monotonic()
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()
    # Run the tailer for the specified duration.
    while time.monotonic() - start_time < duration:
        output_buffer = BytesIO()
        # A download range of (start, 0) means to read from 'start' to the end.
        await mrd.download_ranges([(start_byte, 0, output_buffer)])

        bytes_downloaded = output_buffer.getbuffer().nbytes
        if bytes_downloaded > 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            print(
                f"[{now}] Tailer read {bytes_downloaded} new bytes: {output_buffer.getvalue()}"
            )
            start_byte += bytes_downloaded

        await asyncio.sleep(0.1)  # Poll for new data every second.
    print("Tailer finished.")


async def main_async(bucket_name: str, object_name: str, duration: int):
    """Main function to create an appendable object and run tasks."""
    grpc_client = AsyncGrpcClient().grpc_client
    writer = AsyncAppendableObjectWriter(
        client=grpc_client,
        bucket_name=bucket_name,
        object_name=object_name,
    )
    # 1. Create an empty appendable object.
    try:
        # 1. Create an empty appendable object.
        await writer.open()
        print(f"Created empty appendable object: {object_name}")

        # 2. Create the appender and tailer coroutines.
        appender_task = asyncio.create_task(appender(writer, duration))
        # # Add a small delay to ensure the object is created before tailing begins.
        # await asyncio.sleep(1)
        tailer_task = asyncio.create_task(tailer(bucket_name, object_name, duration))

        # 3. Execute the coroutines concurrently.
        await asyncio.gather(appender_task, tailer_task)
    finally:
        if writer._is_stream_open:
            await writer.close()
            print("Writer closed.")


# [END storage_read_appendable_object_tail]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Demonstrates tailing an appendable GCS object.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--bucket_name", help="Your Cloud Storage bucket name.")
    parser.add_argument(
        "--object_name", help="Your Cloud Storage object name to be created."
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration in seconds to run the demo.",
    )

    args = parser.parse_args()

    asyncio.run(main_async(args.bucket_name, args.object_name, args.duration))
