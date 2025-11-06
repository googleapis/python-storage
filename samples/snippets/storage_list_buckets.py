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

# [START storage_list_buckets]
from google.cloud import storage


def list_buckets():
    """Lists all buckets."""

    storage_client = storage.Client()
    buckets_iterator = storage_client.list_buckets()
    if hasattr(buckets_iterator, "unreachable"):
        print("Unreachable locations:", len(buckets_iterator.unreachable))
        for location in buckets_iterator.unreachable:
            print(location)

    for bucket in buckets_iterator:
        print(bucket.name)


# [END storage_list_buckets]


if __name__ == "__main__":
    list_buckets()
