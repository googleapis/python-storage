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

import datetime

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


def test_bucket_lifecycle_rules(storage_client, buckets_to_delete):
    from google.cloud.storage import constants
    from google.cloud.storage.bucket import LifecycleRuleDelete
    from google.cloud.storage.bucket import LifecycleRuleSetStorageClass

    new_bucket_name = _helpers.unique_name("w-lifcycle-rules")
    custom_time_before = datetime.date(2018, 8, 1)
    noncurrent_before = datetime.date(2018, 8, 1)

    with pytest.raises(exceptions.NotFound):
        storage_client.get_bucket(new_bucket_name)

    bucket = storage_client.bucket(new_bucket_name)
    bucket.add_lifecycle_delete_rule(
        age=42,
        number_of_newer_versions=3,
        days_since_custom_time=2,
        custom_time_before=custom_time_before,
        days_since_noncurrent_time=2,
        noncurrent_time_before=noncurrent_before,
    )
    bucket.add_lifecycle_set_storage_class_rule(
        constants.COLDLINE_STORAGE_CLASS,
        is_live=False,
        matches_storage_class=[constants.NEARLINE_STORAGE_CLASS],
    )

    expected_rules = [
        LifecycleRuleDelete(
            age=42,
            number_of_newer_versions=3,
            days_since_custom_time=2,
            custom_time_before=custom_time_before,
            days_since_noncurrent_time=2,
            noncurrent_time_before=noncurrent_before,
        ),
        LifecycleRuleSetStorageClass(
            constants.COLDLINE_STORAGE_CLASS,
            is_live=False,
            matches_storage_class=[constants.NEARLINE_STORAGE_CLASS],
        ),
    ]

    _helpers.retry_429_503(bucket.create)(location="us")
    buckets_to_delete.append(bucket)

    assert bucket.name == new_bucket_name
    assert list(bucket.lifecycle_rules) == expected_rules

    bucket.clear_lifecyle_rules()
    bucket.patch()

    assert list(bucket.lifecycle_rules) == []
