# Copyright 2026 Google LLC
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

# [START storage_update_encryption_enforcement_config]
from google.cloud import storage


def update_encryption_enforcement_config(bucket_name):
    """Updates the encryption enforcement policy for a bucket."""
    # The ID of your GCS bucket with CMEK restricted
    # bucket_name = "your-unique-bucket-name"

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    # Update a specific type (e.g., change GMEK to FullyRestricted)
    bucket.encryption.google_managed_encryption_enforcement_config.restriction_mode = (
        "FullyRestricted"
    )

    # Update another type (e.g., change CMEK to NotRestricted)
    bucket.encryption.customer_managed_encryption_enforcement_config.restriction_mode = (
        "NotRestricted"
    )

    bucket.patch()

    print(f"Encryption enforcement policy updated for bucket {bucket.name}.")
    print(
        "GMEK is now fully restricted, CMEK is now not restricted, and CSEK enforcement has been removed."
    )


# [END storage_update_encryption_enforcement_config]


if __name__ == "__main__":
    update_encryption_enforcement_config(bucket_name="your-unique-bucket-name")
