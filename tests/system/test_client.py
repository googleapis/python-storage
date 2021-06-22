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

import re

import pytest

from google.cloud import exceptions
from . import _helpers


def test_get_service_account_email(storage_client, require_service_account):
    domain = "gs-project-accounts.iam.gserviceaccount.com"
    email = storage_client.get_service_account_email()

    new_style = re.compile(r"service-(?P<projnum>[^@]+)@{}".format(domain))
    old_style = re.compile(r"{}@{}".format(storage_client.project, domain))
    patterns = [new_style, old_style]
    matches = [pattern.match(email) for pattern in patterns]

    assert any(match for match in matches if match is not None)


def test_create_bucket_simple(storage_client, buckets_to_delete):
    new_bucket_name = _helpers.unique_name("a-new-bucket")

    with pytest.raises(exceptions.NotFound):
        storage_client.get_bucket(new_bucket_name)

    created = _helpers.retry_429_503(storage_client.create_bucket)(new_bucket_name)
    buckets_to_delete.append(created)

    assert created.name == new_bucket_name


def test_list_buckets(storage_client, buckets_to_delete):
    buckets_to_create = [
        _helpers.unique_name("new"),
        _helpers.unique_name("newer"),
        _helpers.unique_name("newest"),
    ]
    created_buckets = []

    for bucket_name in buckets_to_create:
        bucket = _helpers.retry_429_503(storage_client.create_bucket)(bucket_name)
        buckets_to_delete.append(bucket)

    all_buckets = storage_client.list_buckets()

    created_buckets = [
        bucket.name for bucket in all_buckets if bucket.name in buckets_to_create
    ]

    assert sorted(created_buckets) == sorted(buckets_to_create)
