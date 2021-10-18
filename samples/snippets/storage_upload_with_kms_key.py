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

# [START storage_upload_with_kms_key]
from google.cloud import storage


def upload_blob_with_kms(
    bucket_name, source_file_name, destination_blob_name, kms_key_name
):
    """Uploads a file to the bucket, encrypting it with the given KMS key."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    # kms_key_name = "projects/PROJ/locations/LOC/keyRings/RING/cryptoKey/KEY"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name, kms_key_name=kms_key_name)
    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {} with encryption key {}.".format(
            source_file_name, destination_blob_name, kms_key_name
        )
    )


# [END storage_upload_with_kms_key]

if __name__ == "__main__":
    upload_blob_with_kms(
        bucket_name=sys.argv[1],
        source_file_name=sys.argv[2],
        destination_blob_name=sys.argv[3],
        kms_key_name=sys.argv[4],
    )
