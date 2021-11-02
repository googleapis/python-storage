#!/usr/bin/env python

# Copyright 2019 Google Inc. All Rights Reserved.
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

import sys

"""Writes a csv into GCS using file-like IO
"""

# [START storage_fileio_write_blob]
from google.cloud import storage


def write_blob(bucket_name, blob_name):
    """Writes a blob (csv here) to GCS using file-like IO"""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # blob_name = "storage-object-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(blob_name)

    with blob.open("w") as f:
        import csv
        import random
        csv_writer = csv.writer(f)
        csv_writer.writerow([random.random() for x in range(10)])

    print(
        "Wrote csv to storage object {} in bucket {}.".format(
            blob_name, bucket_name
        )
    )


# [END storage_fileio_read_blob]

if __name__ == "__main__":
    write_blob(
        bucket_name=sys.argv[1],
        blob_name=sys.argv[2]
    )
