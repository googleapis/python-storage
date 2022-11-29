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

# [START storage_delete_file]
from google.cloud import storage


def delete_blob(bucket_name, blob_name, generation_match_precondition):
    """Deletes a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"
    # generation_match_precondition = 0

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Optional:
    # Set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the ifGenerationMatch precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    blob.delete(if_generation_match=generation_match_precondition)

    print(f"Blob {blob_name} deleted.")


# [END storage_delete_file]

if __name__ == "__main__":
    delete_blob(bucket_name=sys.argv[1], blob_name=sys.argv[2])
