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

# [START storage_get_soft_deleted_bucket]

from google.cloud import storage

def get_soft_deleted_bucket(bucket_name, generation):
    """Prints out a soft-delted bucket's metadata.

    Args:
        bucket: str
            The bucket resource to pass or name to create.

        generation:
            The generation of the bucket.
    
    """
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name, soft_deleted=True, generation=generation)

    print(f"ID: {bucket.id}")
    print(f"Name: {bucket.name}")
    print(f"Soft Delete time: {bucket.soft_delete_time}")
    print(f"Hard Delete Time : {bucket.hard_delete_time}")


if __name__ == "__main__":
    get_soft_deleted_bucket(bucket_name=sys.argv[1], generation=sys.argv[2])

# [END storage_get_soft_deleted_bucket]