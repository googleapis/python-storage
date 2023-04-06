# Copyright 2017 Google, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import backoff
import os
import tempfile

from google.api_core.exceptions import GoogleAPIError
from google.api_core.exceptions import NotFound
from google.cloud import storage
import pytest

import storage_disable_requester_pays
import storage_download_file_requester_pays
import storage_enable_requester_pays
import storage_get_requester_pays_status


# We use the fixture bucket `requester_pays_bucket`, different from other tests.
# The service account for the test needs to have Billing Project Manager role
# in order to make changes on buckets with requester pays enabled.
PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
BLOB_NAME = "storage_snippets_test_rpays_test"
RPAYS_BUCKET_NAME = os.environ["REQUESTER_PAYS_TEST_BUCKET"]


@pytest.fixture(scope="module")
def requester_pays_bucket():
    """Yields a bucket used for requester pays tests."""
    bucket = storage.Client().bucket(RPAYS_BUCKET_NAME)
    if not bucket.exists():
        bucket.create()
    # Upload a blob for test_download_file_requester_pays
    blob = bucket.blob(BLOB_NAME)
    blob.upload_from_string("Hello, is it me you're looking for?")

    yield bucket

    try:
        bucket.delete(force=True)
    except NotFound:  # race
        pass


@backoff.on_exception(backoff.expo, GoogleAPIError, max_time=60)
def test_enable_requester_pays(requester_pays_bucket, capsys):
    storage_enable_requester_pays.enable_requester_pays(requester_pays_bucket.name)
    out, _ = capsys.readouterr()
    assert f"Requester Pays has been enabled for {requester_pays_bucket.name}" in out


@backoff.on_exception(backoff.expo, GoogleAPIError, max_time=60)
def test_download_file_requester_pays(requester_pays_bucket):
    with tempfile.NamedTemporaryFile() as dest_file:
        storage_download_file_requester_pays.download_file_requester_pays(
            requester_pays_bucket.name, PROJECT, BLOB_NAME, dest_file.name
        )

        assert dest_file.read()


@backoff.on_exception(backoff.expo, GoogleAPIError, max_time=60)
def test_disable_requester_pays(requester_pays_bucket, capsys):
    storage_disable_requester_pays.disable_requester_pays(requester_pays_bucket.name, PROJECT)
    out, _ = capsys.readouterr()
    assert f"Requester Pays has been disabled for {requester_pays_bucket.name}" in out


@backoff.on_exception(backoff.expo, GoogleAPIError, max_time=60)
def test_get_requester_pays_status(requester_pays_bucket, capsys):
    storage_get_requester_pays_status.get_requester_pays_status(requester_pays_bucket.name)
    out, _ = capsys.readouterr()
    assert f"Requester Pays is disabled for {requester_pays_bucket.name}" in out
