#!/usr/bin/env python

# Copyright 2021 Google LLC
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

import os
import sys
import time

# [START storage_file_upload_from_memory]
from google.cloud import storage


def upload_blob_from_memory(bucket_name, destination_blob_name, size_in_mb=1):
    """Uploads a file to the bucket."""

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The contents to upload to the file
    # contents = "these are my contents"

    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    bytes_to_upload = int(size_in_mb * 1024 * 1024)
    contents = os.urandom(bytes_to_upload)

    start_time = time.time_ns()
    blob.upload_from_string(contents)
    end_time = time.time_ns()

    total_bytes_uploaded = len(contents)
    # Time is in nanoseconds, convert to seconds for printing
    total_time_taken_ns = end_time - start_time
    total_time_taken_s = total_time_taken_ns / 1_000_000_000

    if total_time_taken_ns > 0:
        # Throughput calculation using nanoseconds
        throughput_mb_s = (
            total_bytes_uploaded / (total_time_taken_ns / 1_000_000_000)
        ) / (1024 * 1024)
    else:
        throughput_mb_s = float("inf")  # Avoid division by zero

    print(f"Uploaded {total_bytes_uploaded} bytes in {total_time_taken_s:.9f} seconds.")
    print(f"Throughput: {throughput_mb_s:.2f} MB/s")


# [END storage_file_upload_from_memory]


if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print(
            f"Usage: {sys.argv[0]} <bucket_name> <destination_blob_name> [size_in_mb]"
        )
        sys.exit(1)

    bucket_name = sys.argv[1]
    destination_blob_name = sys.argv[2]
    size_mb = 1
    if len(sys.argv) == 4:
        try:
            size_mb = float(sys.argv[3])
        except ValueError:
            print("Please provide a valid number for size_in_mb.")
            sys.exit(1)

    upload_blob_from_memory(
        bucket_name=bucket_name,
        destination_blob_name=destination_blob_name,
        size_in_mb=size_mb,
    )
