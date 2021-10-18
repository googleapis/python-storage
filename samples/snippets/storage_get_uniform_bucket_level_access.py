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

# [START storage_get_uniform_bucket_level_access]
from google.cloud import storage


def get_uniform_bucket_level_access(bucket_name):
    """Get uniform bucket-level access for a bucket"""
    # bucket_name = "my-bucket"

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    iam_configuration = bucket.iam_configuration

    if iam_configuration.uniform_bucket_level_access_enabled:
        print(
            "Uniform bucket-level access is enabled for {}.".format(
                bucket.name
            )
        )
        print(
            "Bucket will be locked on {}.".format(
                iam_configuration.uniform_bucket_level_locked_time
            )
        )
    else:
        print(
            "Uniform bucket-level access is disabled for {}.".format(
                bucket.name
            )
        )


# [END storage_get_uniform_bucket_level_access]

if __name__ == "__main__":
    get_uniform_bucket_level_access(bucket_name=sys.argv[1])
