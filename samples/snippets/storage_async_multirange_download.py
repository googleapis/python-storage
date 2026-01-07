# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

"""Asynchronously download a file in multiple ranges."""
import asyncio

from google.cloud import storage


async def async_multirange_download(
    bucket_name: str, blob_name: str, destination_file_name: str
) -> None:
    """Asynchronously download a file in multiple ranges"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Define the ranges to download (start, end)
    ranges = [(0, 99), (100, 199), (200, 299)]

    # Create the downloader
    downloader = storage.AsyncMultiRangeDownloader()

    # Add the ranges to the downloader
    for start, end in ranges:
        downloader.add_range(start, end)

    # Download the ranges
    await downloader.download_to_file(blob, destination_file_name)

    print(f"Downloaded {destination_file_name} from {blob_name} in multiple ranges.")


if __name__ == "__main__":
    asyncio.run(
        async_multirange_download(
            bucket_name="your-bucket-name",
            blob_name="your-blob-name",
            destination_file_name="destination.txt",
        )
    )


