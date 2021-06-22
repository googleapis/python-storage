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
    shared_bucket, blobs_to_delete, file_data, service_account,
):
    blob = shared_bucket.blob("LargeFile")

    info = file_data["big"]
    with open(info["path"], "rb") as file_obj:
        blob.upload_from_file(file_obj)
        blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_large_file_write_from_stream_w_checksum(
    shared_bucket, blobs_to_delete, file_data, service_account,
):
    blob = shared_bucket.blob("LargeFile")

    info = file_data["big"]
    with open(info["path"], "rb") as file_obj:
        blob.upload_from_file(file_obj, checksum="crc32c")
        blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_large_file_write_from_stream_w_failed_checksum(
    shared_bucket, blobs_to_delete, file_data, service_account,
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
    storage_client, shared_bucket, blobs_to_delete, file_data, service_account,
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
    shared_bucket, blobs_to_delete, file_data, service_account,
):
    blob = shared_bucket.blob("SmallFile")

    info = file_data["simple"]
    blob.upload_from_filename(info["path"])
    blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_small_file_write_from_filename_with_checksum(
    shared_bucket, blobs_to_delete, file_data, service_account,
):
    blob = shared_bucket.blob("SmallFile")

    info = file_data["simple"]
    blob.upload_from_filename(info["path"], checksum="crc32c")
    blobs_to_delete.append(blob)

    _check_blob_hash(blob, info)


def test_small_file_write_from_filename_with_failed_checksum(
    shared_bucket, blobs_to_delete, file_data, service_account,
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


def test_blob_crud_w_user_project(
    storage_client,
    shared_bucket,
    blobs_to_delete,
    file_data,
    service_account,
    user_project,
):
    gen1_payload = b"gen1"
    with_user_project = storage_client.bucket(
        shared_bucket.name, user_project=user_project
    )
    blob = with_user_project.blob("SmallFile")

    info = file_data["simple"]
    with open(info["path"], mode="rb") as to_read:
        gen0_payload = to_read.read()

    # Exercise 'objects.insert' w/ userProject.
    blob.upload_from_filename(info["path"])
    gen0 = blob.generation

    # Upload a second generation of the blob
    blob.upload_from_string(gen1_payload)
    gen1 = blob.generation

    blob0 = with_user_project.blob("SmallFile", generation=gen0)
    blob1 = with_user_project.blob("SmallFile", generation=gen1)

    # Exercise 'objects.get' w/ generation
    assert with_user_project.get_blob(blob.name).generation == gen1
    assert with_user_project.get_blob(blob.name, generation=gen0).generation == gen0

    try:
        # Exercise 'objects.get' (metadata) w/ userProject.
        assert blob.exists()
        blob.reload()

        # Exercise 'objects.get' (media) w/ userProject.
        assert blob0.download_as_bytes() == gen0_payload
        assert blob1.download_as_bytes() == gen1_payload

        # Exercise 'objects.patch' w/ userProject.
        blob0.content_language = "en"
        blob0.patch()
        assert blob0.content_language == "en"
        assert blob1.content_language is None

        # Exercise 'objects.update' w/ userProject.
        metadata = {"foo": "Foo", "bar": "Bar"}
        blob0.metadata = metadata
        blob0.update()
        assert blob0.metadata == metadata
        assert blob1.metadata is None

    finally:
        # Exercise 'objects.delete' (metadata) w/ userProject.
        blobs = storage_client.list_blobs(
            with_user_project, prefix=blob.name, versions=True
        )
        assert [each.generation for each in blobs] == [gen0, gen1]

        blob0.delete()
        blobs = storage_client.list_blobs(
            with_user_project, prefix=blob.name, versions=True
        )
        assert [each.generation for each in blobs] == [gen1]

        blob1.delete()


def test_blob_crud_w_generation_match(
    shared_bucket, blobs_to_delete, file_data, service_account,
):
    wrong_generation_number = 6
    wrong_metageneration_number = 9
    gen1_payload = b"gen1"

    blob = shared_bucket.blob("SmallFile")

    info = file_data["simple"]
    with open(info["path"], mode="rb") as to_read:
        gen0_payload = to_read.read()

    blob.upload_from_filename(info["path"])
    gen0 = blob.generation

    # Upload a second generation of the blob
    blob.upload_from_string(gen1_payload)
    gen1 = blob.generation

    blob0 = shared_bucket.blob("SmallFile", generation=gen0)
    blob1 = shared_bucket.blob("SmallFile", generation=gen1)

    try:
        # Exercise 'objects.get' (metadata) w/ generation match.
        with pytest.raises(exceptions.PreconditionFailed):
            blob.exists(if_generation_match=wrong_generation_number)

        assert blob.exists(if_generation_match=gen1)

        with pytest.raises(exceptions.PreconditionFailed):
            blob.reload(if_metageneration_match=wrong_metageneration_number)

        blob.reload(if_generation_match=gen1)

        # Exercise 'objects.get' (media) w/ generation match.
        assert blob0.download_as_bytes(if_generation_match=gen0) == gen0_payload
        assert blob1.download_as_bytes(if_generation_not_match=gen0) == gen1_payload

        # Exercise 'objects.patch' w/ generation match.
        blob0.content_language = "en"
        blob0.patch(if_generation_match=gen0)

        assert blob0.content_language == "en"
        assert blob1.content_language is None

        # Exercise 'objects.update' w/ generation match.
        metadata = {"foo": "Foo", "bar": "Bar"}
        blob0.metadata = metadata
        blob0.update(if_generation_match=gen0)

        assert blob0.metadata == metadata
        assert blob1.metadata is None
    finally:
        # Exercise 'objects.delete' (metadata) w/ generation match.
        with pytest.raises(exceptions.PreconditionFailed):
            blob0.delete(if_metageneration_match=wrong_metageneration_number)

        blob0.delete(if_generation_match=gen0)
        blob1.delete(if_metageneration_not_match=wrong_metageneration_number)


def test_blob_acl_w_user_project(
    storage_client,
    shared_bucket,
    blobs_to_delete,
    file_data,
    service_account,
    user_project,
):
    with_user_project = storage_client.bucket(
        shared_bucket.name, user_project=user_project
    )
    blob = with_user_project.blob("SmallFile")

    info = file_data["simple"]

    blob.upload_from_filename(info["path"])
    blobs_to_delete.append(blob)

    # Exercise blob ACL w/ userProject
    acl = blob.acl
    acl.reload()
    acl.all().grant_read()
    acl.save()
    assert "READER" in acl.all().get_roles()

    del acl.entities["allUsers"]
    acl.save()
    assert not acl.has_entity("allUsers")


def test_blob_acl_upload_predefined(
    shared_bucket, blobs_to_delete, file_data, service_account,
):
    control = shared_bucket.blob("logo")
    control_info = file_data["logo"]

    blob = shared_bucket.blob("SmallFile")
    info = file_data["simple"]

    try:
        control.upload_from_filename(control_info["path"])
    finally:
        blobs_to_delete.append(control)

    try:
        blob.upload_from_filename(info["path"], predefined_acl="publicRead")
    finally:
        blobs_to_delete.append(blob)

    control_acl = control.acl
    assert "READER" not in control_acl.all().get_roles()

    acl = blob.acl
    assert "READER" in acl.all().get_roles()

    acl.all().revoke_read()
    assert acl.all().get_roles() == set()
    assert control_acl.all().get_roles() == acl.all().get_roles()


def test_blob_patch_metadata(
    shared_bucket, blobs_to_delete, file_data, service_account,
):
    filename = file_data["logo"]["path"]
    blob_name = os.path.basename(filename)

    blob = shared_bucket.blob(blob_name)
    blob.upload_from_filename(filename)
    blobs_to_delete.append(blob)

    # NOTE: This should not be necessary. We should be able to pass
    #       it in to upload_file and also to upload_from_string.
    blob.content_type = "image/png"
    assert blob.content_type == "image/png"

    metadata = {"foo": "Foo", "bar": "Bar"}
    blob.metadata = metadata
    blob.patch()
    blob.reload()
    assert blob.metadata == metadata

    # Ensure that metadata keys can be deleted by setting equal to None.
    new_metadata = {"foo": "Foo", "bar": None}
    blob.metadata = new_metadata
    blob.patch()
    blob.reload()
    assert blob.metadata == {"foo": "Foo"}


def test_blob_direct_write_and_read_into_file(
    shared_bucket, blobs_to_delete, service_account,
):
    payload = b"Hello World"
    blob = shared_bucket.blob("MyBuffer")
    blob.upload_from_string(payload)
    blobs_to_delete.append(blob)

    same_blob = shared_bucket.blob("MyBuffer")
    same_blob.reload()  # Initialize properties.

    with tempfile.NamedTemporaryFile() as temp_f:

        with open(temp_f.name, "wb") as file_obj:
            same_blob.download_to_file(file_obj)

        with open(temp_f.name, "rb") as file_obj:
            stored_contents = file_obj.read()

    assert stored_contents == payload