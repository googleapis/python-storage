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

import os
import tempfile

import pytest
import six
import mock

from google import resumable_media
from google.api_core import exceptions
from google.cloud.storage._helpers import _base64_md5hash
from . import _helpers

dirname = os.path.realpath(os.path.dirname(__file__))
data_dirname = os.path.abspath(os.path.join(dirname, "..", "data"))
_filenames = [
    ("logo", "CloudPlatform_128px_Retina.png"),
    ("big", "five-point-one-mb-file.zip"),
    ("simple", "simple.txt"),
]
_file_data = {
    key: {"path": os.path.join(data_dirname, file_name)}
    for key, file_name in _filenames
}
encryption_key = "b23ff11bba187db8c37077e6af3b25b8"


@pytest.fixture(scope="session")
def file_data():
    for file_data in _file_data.values():
        with open(file_data["path"], "rb") as file_obj:
            file_data["hash"] = _base64_md5hash(file_obj)

    return _file_data


def _check_blob_hash(blob, info):
    md5_hash = blob.md5_hash
    if not isinstance(md5_hash, six.binary_type):
        md5_hash = md5_hash.encode("utf-8")

    assert md5_hash == info["hash"]


def test_large_file_write_from_stream(
    shared_bucket, blobs_to_delete, file_data, require_service_account,
):
    blob = shared_bucket.blob("LargeFile")

    info = file_data["big"]
    with open(info["path"], "rb") as file_obj:
        blob.upload_from_file(file_obj)
        blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_large_file_write_from_stream_w_checksum(
    shared_bucket, blobs_to_delete, file_data, require_service_account,
):
    blob = shared_bucket.blob("LargeFile")

    info = file_data["big"]
    with open(info["path"], "rb") as file_obj:
        blob.upload_from_file(file_obj, checksum="crc32c")
        blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_large_file_write_from_stream_w_failed_checksum(
    shared_bucket, blobs_to_delete, file_data, require_service_account,
):
    blob = shared_bucket.blob("LargeFile")

    # Intercept the digest processing at the last stage and replace it
    # with garbage.  This is done with a patch to monkey-patch the
    # resumable media library's checksum # processing;
    # it does not mock a remote interface like a unit test would.
    # The # remote API is still exercised.
    info = file_data["big"]
    with open(info["path"], "rb") as file_obj:

        with mock.patch(
            "google.resumable_media._helpers.prepare_checksum_digest",
            return_value="FFFFFF==",
        ):
            with pytest.raises(resumable_media.DataCorruption):
                blob.upload_from_file(file_obj, checksum="crc32c")

    assert not blob.exists()


def test_large_file_write_from_stream_w_encryption_key(
    storage_client, shared_bucket, blobs_to_delete, file_data, require_service_account,
):
    blob = shared_bucket.blob("LargeFile", encryption_key=encryption_key)

    info = file_data["big"]
    with open(info["path"], "rb") as file_obj:
        blob.upload_from_file(file_obj)
        blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)

    with tempfile.NamedTemporaryFile() as temp_f:
        with open(temp_f.name, "wb") as file_obj:
            storage_client.download_blob_to_file(blob, file_obj)

        with open(temp_f.name, "rb") as file_obj:
            md5_temp_hash = _base64_md5hash(file_obj)

    assert md5_temp_hash == info["hash"]


def test_small_file_write_from_filename(
    shared_bucket, blobs_to_delete, file_data, require_service_account,
):
    blob = shared_bucket.blob("SmallFile")

    info = file_data["simple"]
    blob.upload_from_filename(info["path"])
    blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_small_file_write_from_filename_with_checksum(
    shared_bucket, blobs_to_delete, file_data, require_service_account,
):
    blob = shared_bucket.blob("SmallFile")

    info = file_data["simple"]
    blob.upload_from_filename(info["path"], checksum="crc32c")
    blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_small_file_write_from_filename_with_failed_checksum(
    shared_bucket, blobs_to_delete, file_data, require_service_account,
):
    blob = shared_bucket.blob("SmallFile")

    info = file_data["simple"]
    # Intercept the digest processing at the last stage and replace
    # it with garbage
    with mock.patch(
        "google.resumable_media._helpers.prepare_checksum_digest",
        return_value="FFFFFF==",
    ):
        with pytest.raises(exceptions.BadRequest):
            blob.upload_from_filename(info["path"], checksum="crc32c")

    assert not blob.exists()
