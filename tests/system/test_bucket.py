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


def test_bucket_update_labels(storage_client, buckets_to_delete):
    bucket_name = _helpers.unique_name("update-labels")
    bucket = _helpers.retry_429_503(storage_client.create_bucket)(bucket_name)
    buckets_to_delete.append(bucket)
    assert bucket.exists()

    updated_labels = {"test-label": "label-value"}
    bucket.labels = updated_labels
    bucket.update()
    assert bucket.labels == updated_labels

    new_labels = {"another-label": "another-value"}
    bucket.labels = new_labels
    bucket.patch()
    assert bucket.labels == new_labels

    bucket.labels = {}
    bucket.update()
    assert bucket.labels == {}


def test_bucket_get_set_iam_policy(storage_client, buckets_to_delete):
    from google.cloud.storage.iam import STORAGE_OBJECT_VIEWER_ROLE
    from google.api_core.exceptions import BadRequest
    from google.api_core.exceptions import PreconditionFailed

    bucket_name = _helpers.unique_name("iam-policy")
    bucket = _helpers.retry_429_503(storage_client.create_bucket)(bucket_name)
    buckets_to_delete.append(bucket)
    assert bucket.exists()

    policy_no_version = bucket.get_iam_policy()
    assert policy_no_version.version == 1

    policy = bucket.get_iam_policy(requested_policy_version=3)
    assert policy == policy_no_version

    member = "serviceAccount:{}".format(storage_client.get_service_account_email())

    binding_w_condition = {
        "role": STORAGE_OBJECT_VIEWER_ROLE,
        "members": {member},
        "condition": {
            "title": "always-true",
            "description": "test condition always-true",
            "expression": "true",
        },
    }
    policy.bindings.append(binding_w_condition)

    with pytest.raises(PreconditionFailed, match="enable uniform bucket-level access"):
        bucket.set_iam_policy(policy)

    bucket.iam_configuration.uniform_bucket_level_access_enabled = True
    bucket.patch()

    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.bindings.append(binding_w_condition)

    with pytest.raises(BadRequest, match="at least 3"):
        bucket.set_iam_policy(policy)

    policy.version = 3
    returned_policy = bucket.set_iam_policy(policy)
    assert returned_policy.version == 3
    assert returned_policy.bindings == policy.bindings

    fetched_policy = bucket.get_iam_policy(requested_policy_version=3)
    assert fetched_policy.bindings == returned_policy.bindings
