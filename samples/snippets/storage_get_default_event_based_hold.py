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

# [START storage_get_default_event_based_hold]
from google.cloud import storage


def get_default_event_based_hold(bucket_name):
    """Gets the default event based hold on a given bucket"""
    # bucket_name = "my-bucket"

    storage_client = storage.Client()

    bucket = storage_client.get_bucket(bucket_name)

    if bucket.default_event_based_hold:
        print("Default event-based hold is enabled for {}".format(bucket_name))
    else:
        print(
            "Default event-based hold is not enabled for {}".format(
                bucket_name
            )
        )


# [END storage_get_default_event_based_hold]


if __name__ == "__main__":
    get_default_event_based_hold(bucket_name=sys.argv[1])
