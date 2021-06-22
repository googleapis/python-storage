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

import contextlib

import pytest

from . import _helpers


@pytest.fixture(scope="session")
def storage_client():
    from google.cloud.storage import Client

    client = Client()
    with contextlib.closing(client):
        yield client


@pytest.fixture(scope="session")
def shared_bucket_name():
    return _helpers.unique_name("gcp-systest")


@pytest.fixture(scope="session")
def shared_bucket(storage_client, shared_bucket_name):
    bucket = storage_client.bucket(shared_bucket_name)
    bucket.versioning_enabled = True
    _helpers.retry_429_503(bucket.create)()

    yield bucket

    _helpers.delete_bucket(bucket)


@pytest.fixture(scope="session")
def user_project():
    if _helpers.user_project is None:
        pytest.skip("USER_PROJECT not set in environment.")
    return _helpers.user_project


@pytest.fixture(scope="session")
def service_account(storage_client):
    from google.oauth2.service_account import Credentials

    if not isinstance(storage_client._credentials, Credentials):
        pytest.skip("These tests require a service account credential")
    return storage_client._credentials


@pytest.fixture(scope="function")
def buckets_to_delete():
    buckets_to_delete = []

    yield buckets_to_delete

    for bucket in buckets_to_delete:
        _helpers.delete_bucket(bucket)


@pytest.fixture(scope="function")
def blobs_to_delete():
    blobs_to_delete = []

    yield blobs_to_delete

    for blob in blobs_to_delete:
        _helpers.delete_blob(blob)
