#!/usr/bin/env python

# Copyright 2021 Google LLC
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

"""Sample that creates a new bucket in a specified region
"""

# [START storage_set_client_endpoint]

from google.cloud import storage


def set_client_endpoint(api_endpoint):
    """Initiates client with specified endpoint."""
    # api_endpoint = 'https://storage.googleapis.com'

    storage_client = storage.Client(client_options={'api_endpoint': api_endpoint})

    print(f"client initiated with endpoint: {storage_client._connection.API_BASE_URL}")

    return storage_client


# [END storage_set_client_endpoint]

if __name__ == "__main__":
    set_client_endpoint(api_endpoint=sys.argv[1])
