#!/usr/bin/env python

# Copyright 2022 Google LLC. All Rights Reserved.
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

"""
Sample that creates a dual region bucket.
"""

# [START storage_create_bucket_dual_region]
from google.cloud import storage


def create_bucket_dual_region(bucket_name, region_1, region_2):
    """Creates a Dual-Region Bucket with provided locations."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The bucket's pair of regions. Case-insensitive.
    # See this documentation for other valid locations:
    # https://cloud.google.com/storage/docs/locations
    # region_1 = "US-EAST1"
    # region_2 = "US-WEST1"

    storage_client = storage.Client()
    storage_client.create_bucket(bucket_name, location=f"{region_1}+{region_2}")

    print(f"Bucket {bucket_name} created in {region_1}+{region_2}.")

# [END storage_create_bucket_dual_region]


if __name__ == "__main__":
    create_bucket_dual_region(bucket_name=sys.argv[1], region_1=sys.argv[2], region_2=sys.argv[3])