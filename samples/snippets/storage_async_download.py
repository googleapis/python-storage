#!/usr/bin/env python

# Copyright 2025 Google LLC.
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

import asyncio
import sys


"""Sample that asynchronously downloads multiple files from GCS to application's memory.
"""


# [START storage_async_download]
# This sample can be run by calling `async.run(async_download_blobs('bucket_name'))`
async def async_download_blobs(bucket_name):
    """Downloads a number of files in parallel from the bucket;
        assuming files with prefix `async_sample_blob_%d` exits in bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    import asyncio
    from google.cloud import storage

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    loop = asyncio.get_running_loop()

    tasks = []
    count = 3
    for x in range(count):
        blob_name = f"async_sample_blob_{x}"
        blob = bucket.blob(blob_name)
        # The first arg, None, tells it to use the default loops executor
        tasks.append(loop.run_in_executor(None, blob.download_as_bytes))

    # If the method returns a value (such as download_as_bytes), gather will return the values
    _ = await asyncio.gather(*tasks)
    for x in range(count):
        print(f"Downloaded storage object async_sample_blob_{x}")


# [END storage_async_download]


if __name__ == "__main__":
    asyncio.run(async_download_blobs(
        bucket_name=sys.argv[1]
    ))
