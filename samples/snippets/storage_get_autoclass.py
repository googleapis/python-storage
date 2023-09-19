#!/usr/bin/env python

# Copyright 2022 Google LLC
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

# [START storage_get_autoclass]
from google.cloud import storage


def get_autoclass(bucket_name):
    """Get the Autoclass setting for a bucket."""
    # The ID of your GCS bucket
    # bucket_name = "my-bucket"

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    autoclass_enabled = bucket.autoclass_enabled
    autoclass_toggle_time = bucket.autoclass_toggle_time
    terminal_storage_class = bucket.autoclass_terminal_storage_class
    tsc_update_time = bucket.autoclass_terminal_storage_class_update_time

    print(f"Autoclass enabled is set to {autoclass_enabled} for {bucket.name} at {autoclass_toggle_time}.")
    print(f"Autoclass terminal storage class is set to {terminal_storage_class} for {bucket.name} at {tsc_update_time}.")

    return bucket


# [END storage_get_autoclass]

if __name__ == "__main__":
    get_autoclass(bucket_name=sys.argv[1])
