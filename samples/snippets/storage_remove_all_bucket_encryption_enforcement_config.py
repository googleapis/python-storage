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

from google.cloud import storage

# [START storage_remove_all_bucket_encryption_enforcement_config]
def remove_all_bucket_encryption_enforcement_config(bucket_name):
    """Removes all bucket encryption enforcement configuration."""
    # The ID of your GCS bucket
    # bucket_name = "your-unique-bucket-name"

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    bucket.customer_managed_encryption_enforcement_config = None
    bucket.customer_supplied_encryption_enforcement_config = None
    bucket.google_managed_encryption_enforcement_config = None
    bucket.patch()

    print(f"Removed Encryption Enforcement Config from bucket {bucket.name}.")

# [END storage_remove_all_bucket_encryption_enforcement_config]

if __name__ == "__main__":
    remove_all_bucket_encryption_enforcement_config(bucket_name="your-unique-bucket-name")
