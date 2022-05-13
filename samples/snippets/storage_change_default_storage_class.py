#!/usr/bin/env python

# Copyright 2020 Google LLC. All Rights Reserved.
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

# [START storage_change_default_storage_class]
from google.cloud import storage
from google.cloud.storage import constants


def change_default_storage_class(bucket_name):
    """Change the default storage class of the bucket"""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    bucket = storage_client.get_bucket(bucket_name)
    bucket.storage_class = constants.COLDLINE_STORAGE_CLASS
    bucket.patch()

    print(f"Default storage class for bucket {bucket_name} has been set to {bucket.storage_class}")
    return bucket


# [END storage_change_default_storage_class]

if __name__ == "__main__":
    change_default_storage_class(bucket_name=sys.argv[1])
