#!/usr/bin/env python

# Copyright 2025 Google Inc. All Rights Reserved.
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

from google.cloud import storage

# [START storage_set_soft_delete_policy]


def set_soft_delete_policy(bucket_name, duration_in_seconds):
    """Sets a soft-delete policy on the bucket"""
    # bucket_name = "your-bucket-name"
    # duration_in_seconds = "your-soft-delete-retention-duration-in-seconds"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    bucket.soft_delete_policy.retention_duration_seconds = duration_in_seconds
    bucket.patch()

    print(
        f"Object soft-delete duration is updated to {duration_in_seconds} seconds in the bucket {bucket_name}"
    )


# [END storage_set_soft_delete_policy]

if __name__ == "__main__":
    set_soft_delete_policy(bucket_name=sys.argv[1], duration_in_seconds=sys.argv[2])
