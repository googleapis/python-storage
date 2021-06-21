# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from google.api_core import exceptions
from . import _helpers


def test_bucket_create_w_alt_storage_class(storage_client, buckets_to_delete):
    from google.cloud.storage import constants

    new_bucket_name = _helpers.unique_name("bucket-w-archive")

    with pytest.raises(exceptions.NotFound):
        storage_client.get_bucket(new_bucket_name)

    bucket = storage_client.bucket(new_bucket_name)
    bucket.storage_class = constants.ARCHIVE_STORAGE_CLASS

    _helpers.retry_429_503(bucket.create)()
    buckets_to_delete.append(bucket)

    created = storage_client.get_bucket(new_bucket_name)
    assert created.storage_class == constants.ARCHIVE_STORAGE_CLASS
