# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

import os
import uuid

import pytest

from google.auth.credentials import AnonymousCredentials
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud.storage._helpers import _base64_md5hash


"""Environment variable or default host for Storage testbench emulator."""
_HOST = os.environ.get("STORAGE_EMULATOR_HOST", "http://localhost:9000")


"""Emulated project information for the storage testbench."""
_CONF_TEST_PROJECT_ID = "my-project-id"
_CONF_TEST_SERVICE_ACCOUNT_EMAIL = (
    "my-service-account@my-project-id.iam.gserviceaccount.com"
)
_CONF_TEST_PUBSUB_TOPIC_NAME = "my-topic-name"


"""Utilize shared test data."""
dirname = os.path.realpath(os.path.dirname(__file__))
data_dirname = os.path.abspath(os.path.join(dirname, "..", "data"))
_filenames = [
    ("logo", "CloudPlatform_128px_Retina.png"),
    ("simple", "simple.txt"),
    ("big", "five-point-one-mb-file.zip"),
]
_file_data = {
    key: {"path": os.path.join(data_dirname, file_name)}
    for key, file_name in _filenames
}

_STRING_CONTENT = "hello world"


########################################################################################################################################
### Pytest Fixtures to Populate Retry Conformance Test Resources #######################################################################
########################################################################################################################################


@pytest.fixture
def client():
    client = storage.Client(
        project=_CONF_TEST_PROJECT_ID,
        credentials=AnonymousCredentials(),
        client_options={"api_endpoint": _HOST},
    )
    return client


@pytest.fixture
def bucket(client):
    bucket = client.bucket(uuid.uuid4().hex)
    client.create_bucket(bucket)
    yield bucket
    try:
        bucket.delete(force=True)
    except NotFound:  # in cases where bucket is deleted within the test
        pass


@pytest.fixture
def object(client, bucket):
    blob = client.bucket(bucket.name).blob(uuid.uuid4().hex)
    blob.upload_from_string(_STRING_CONTENT)
    blob.reload()
    yield blob
    try:
        blob.delete()
    except NotFound:  # in cases where object is deleted within the test
        pass


@pytest.fixture
def notification(client, bucket):
    notification = client.bucket(bucket.name).notification(
        topic_name=_CONF_TEST_PUBSUB_TOPIC_NAME
    )
    notification.create()
    notification.reload()
    yield notification
    try:
        notification.delete()
    except NotFound:  # in cases where notification is deleted within the test
        pass


@pytest.fixture
def hmac_key(client):
    hmac_key, _secret = client.create_hmac_key(
        service_account_email=_CONF_TEST_SERVICE_ACCOUNT_EMAIL,
        project_id=_CONF_TEST_PROJECT_ID,
    )
    yield hmac_key
    try:
        hmac_key.state = "INACTIVE"
        hmac_key.update()
        hmac_key.delete()
    except NotFound:  # in cases where hmac_key is deleted within the test
        pass


@pytest.fixture
def file_data():
    for file_data in _file_data.values():
        with open(file_data["path"], "rb") as file_obj:
            file_data["hash"] = _base64_md5hash(file_obj)

    return _file_data
