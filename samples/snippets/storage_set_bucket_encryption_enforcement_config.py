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
from google.cloud.storage.bucket import EncryptionEnforcementConfig


# [START storage_set_bucket_encryption_enforcement_config]
def set_bucket_encryption_enforcement_config(bucket_name):
    """Creates a bucket with encryption enforcement configuration."""
    # The ID of your GCS bucket
    # bucket_name = "your-unique-bucket-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Restriction mode can be "FULLY_RESTRICTED" or "NOT_RESTRICTED"
    bucket.customer_managed_encryption_enforcement_config = EncryptionEnforcementConfig(restriction_mode="NOT_RESTRICTED")
    bucket.customer_supplied_encryption_enforcement_config = EncryptionEnforcementConfig(restriction_mode="FULLY_RESTRICTED")
    bucket.google_managed_encryption_enforcement_config = EncryptionEnforcementConfig(restriction_mode="FULLY_RESTRICTED")

    bucket.create()

    print(f"Created bucket {bucket.name} with Encryption Enforcement Config.")
# [END storage_set_bucket_encryption_enforcement_config]


if __name__ == "__main__":
    set_bucket_encryption_enforcement_config(bucket_name="your-unique-bucket-name")
