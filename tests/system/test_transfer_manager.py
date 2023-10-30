# coding=utf-8
# Copyright 2022 Google LLC
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

import tempfile
import os

import pytest

from google.cloud.storage import transfer_manager
from google.cloud.storage._helpers import _base64_md5hash

from google.api_core import exceptions

DEADLINE = 30

encryption_key = "b23ff11bba187db8c37077e6af3b25b8"


def _check_blob_hash(blob, info):
    md5_hash = blob.md5_hash
    if not isinstance(md5_hash, bytes):
        md5_hash = md5_hash.encode("utf-8")

    assert md5_hash == info["hash"]


def test_upload_many(shared_bucket, file_data, blobs_to_delete):
    FILE_BLOB_PAIRS = [
        (file_data["simple"]["path"], shared_bucket.blob("simple1")),
        (file_data["simple"]["path"], shared_bucket.blob("simple2")),
    ]

    results = transfer_manager.upload_many(
        FILE_BLOB_PAIRS,
        worker_type=transfer_manager.PROCESS,
        deadline=DEADLINE,
    )
    assert results == [None, None]

    blobs = shared_bucket.list_blobs()
    for blob in blobs:
        if blob.name.startswith("simple"):
            blobs_to_delete.append(blob)
    assert len(blobs_to_delete) == 2


def test_upload_many_with_threads_and_file_objs(
    shared_bucket, file_data, blobs_to_delete
):
    FILE_BLOB_PAIRS = [
        (open(file_data["simple"]["path"], "rb"), shared_bucket.blob("simple1")),
        (open(file_data["simple"]["path"], "rb"), shared_bucket.blob("simple2")),
    ]

    results = transfer_manager.upload_many(
        FILE_BLOB_PAIRS,
        worker_type=transfer_manager.THREAD,
        deadline=DEADLINE,
    )
    assert results == [None, None]

    blobs = shared_bucket.list_blobs()
    for blob in blobs:
        if blob.name.startswith("simple"):
            blobs_to_delete.append(blob)
    assert len(blobs_to_delete) == 2


def test_upload_many_skip_if_exists(
    listable_bucket, listable_filenames, file_data, blobs_to_delete
):
    FILE_BLOB_PAIRS = [
        (file_data["logo"]["path"], listable_bucket.blob(listable_filenames[0])),
        (file_data["simple"]["path"], listable_bucket.blob("simple")),
    ]

    results = transfer_manager.upload_many(
        FILE_BLOB_PAIRS,
        skip_if_exists=True,
        raise_exception=True,
        deadline=DEADLINE,
    )
    assert isinstance(results[0], exceptions.PreconditionFailed)
    assert results[1] is None

    blobs = listable_bucket.list_blobs()
    for blob in blobs:
        if blob.name.startswith("simple"):
            blobs_to_delete.append(blob)
    assert len(blobs_to_delete) == 1


def test_upload_many_from_filenames_with_attributes(
    listable_bucket, listable_filenames, file_data, blobs_to_delete
):
    SOURCE_DIRECTORY, FILENAME = os.path.split(file_data["logo"]["path"])

    transfer_manager.upload_many_from_filenames(
        listable_bucket,
        [FILENAME],
        source_directory=SOURCE_DIRECTORY,
        additional_blob_attributes={"cache_control": "no-cache"},
        raise_exception=True,
    )

    blob = listable_bucket.blob(FILENAME)
    blob.reload()
    blobs_to_delete.append(blob)
    assert blob.cache_control == "no-cache"


def test_download_many(listable_bucket):
    blobs = list(listable_bucket.list_blobs())
    with tempfile.TemporaryDirectory() as tempdir:
        filenames = [
            os.path.join(tempdir, "file_a.txt"),
            os.path.join(tempdir, "file_b.txt"),
        ]
        BLOB_FILE_PAIRS = zip(blobs[:2], filenames)

        results = transfer_manager.download_many(
            BLOB_FILE_PAIRS,
            worker_type=transfer_manager.PROCESS,
            deadline=DEADLINE,
        )
        assert results == [None, None]
        for count, filename in enumerate(filenames):
            with open(filename, "rb") as fp:
                assert len(fp.read()) == blobs[count].size


def test_download_many_with_threads_and_file_objs(listable_bucket):
    blobs = list(listable_bucket.list_blobs())
    with tempfile.TemporaryFile() as file_a, tempfile.TemporaryFile() as file_b:
        tempfiles = [file_a, file_b]
        BLOB_FILE_PAIRS = zip(blobs[:2], tempfiles)

        results = transfer_manager.download_many(
            BLOB_FILE_PAIRS,
            worker_type=transfer_manager.THREAD,
            deadline=DEADLINE,
        )
        assert results == [None, None]
        for fp in tempfiles:
            assert fp.tell() != 0


def test_download_chunks_concurrently(shared_bucket, file_data):
    # Upload a big file
    source_file = file_data["big"]
    upload_blob = shared_bucket.blob("chunky_file")
    upload_blob.upload_from_filename(source_file["path"])
    upload_blob.reload()
    size = upload_blob.size
    chunk_size = size // 32

    # Get a fresh blob obj w/o metadata for testing purposes
    download_blob = shared_bucket.blob("chunky_file")

    with tempfile.TemporaryDirectory() as tempdir:
        full_filename = os.path.join(tempdir, "chunky_file_1")
        transfer_manager.download_chunks_concurrently(
            download_blob,
            full_filename,
            chunk_size=chunk_size,
            deadline=DEADLINE,
        )
        with open(full_filename, "rb") as file_obj:
            assert _base64_md5hash(file_obj) == source_file["hash"]

        # Now test for case where last chunk is exactly 1 byte.
        trailing_chunk_filename = os.path.join(tempdir, "chunky_file_2")
        transfer_manager.download_chunks_concurrently(
            download_blob,
            trailing_chunk_filename,
            chunk_size=size - 1,
            deadline=DEADLINE,
        )
        with open(trailing_chunk_filename, "rb") as file_obj:
            assert _base64_md5hash(file_obj) == source_file["hash"]

        # And for a case where there is only one chunk.
        trailing_chunk_filename = os.path.join(tempdir, "chunky_file_3")
        transfer_manager.download_chunks_concurrently(
            download_blob,
            trailing_chunk_filename,
            chunk_size=size,
            deadline=DEADLINE,
        )
        with open(trailing_chunk_filename, "rb") as file_obj:
            assert _base64_md5hash(file_obj) == source_file["hash"]

        # Also test threaded mode.
        threaded_filename = os.path.join(tempdir, "chunky_file_4")
        transfer_manager.download_chunks_concurrently(
            download_blob,
            threaded_filename,
            chunk_size=chunk_size,
            deadline=DEADLINE,
            worker_type=transfer_manager.THREAD,
        )
        with open(threaded_filename, "rb") as file_obj:
            assert _base64_md5hash(file_obj) == source_file["hash"]


def test_upload_chunks_concurrently(shared_bucket, file_data, blobs_to_delete):
    source_file = file_data["big"]
    filename = source_file["path"]
    blob_name = "mpu_file"
    upload_blob = shared_bucket.blob(blob_name)
    chunk_size = 5 * 1024 * 1024  # Minimum supported by XML MPU API
    assert os.path.getsize(filename) > chunk_size  # Won't make a good test otherwise

    blobs_to_delete.append(upload_blob)

    transfer_manager.upload_chunks_concurrently(
        filename, upload_blob, chunk_size=chunk_size, deadline=DEADLINE
    )

    with tempfile.NamedTemporaryFile() as tmp:
        download_blob = shared_bucket.blob(blob_name)
        download_blob.download_to_file(tmp)
        tmp.seek(0)

        with open(source_file["path"], "rb") as sf:
            source_contents = sf.read()
            temp_contents = tmp.read()
            assert source_contents == temp_contents

    # Also test threaded mode
    blob_name = "mpu_threaded"
    upload_blob = shared_bucket.blob(blob_name)
    chunk_size = 5 * 1024 * 1024  # Minimum supported by XML MPU API
    assert os.path.getsize(filename) > chunk_size  # Won't make a good test otherwise

    transfer_manager.upload_chunks_concurrently(
        filename,
        upload_blob,
        chunk_size=chunk_size,
        deadline=DEADLINE,
        worker_type=transfer_manager.THREAD,
    )

    with tempfile.NamedTemporaryFile() as tmp:
        download_blob = shared_bucket.blob(blob_name)
        download_blob.download_to_file(tmp)
        tmp.seek(0)

        with open(source_file["path"], "rb") as sf:
            source_contents = sf.read()
            temp_contents = tmp.read()
            assert source_contents == temp_contents


def test_upload_chunks_concurrently_with_metadata(
    shared_bucket, file_data, blobs_to_delete
):
    import datetime
    from google.cloud._helpers import UTC

    now = datetime.datetime.utcnow().replace(tzinfo=UTC)
    custom_metadata = {"key_a": "value_a", "key_b": "value_b"}

    METADATA = {
        "cache_control": "private",
        "content_disposition": "inline",
        "content_language": "en-US",
        "custom_time": now,
        "metadata": custom_metadata,
        "storage_class": "NEARLINE",
    }

    source_file = file_data["big"]
    filename = source_file["path"]
    blob_name = "mpu_file_with_metadata"
    upload_blob = shared_bucket.blob(blob_name)

    for key, value in METADATA.items():
        setattr(upload_blob, key, value)

    chunk_size = 5 * 1024 * 1024  # Minimum supported by XML MPU API
    assert os.path.getsize(filename) > chunk_size  # Won't make a good test otherwise

    transfer_manager.upload_chunks_concurrently(
        filename, upload_blob, chunk_size=chunk_size, deadline=DEADLINE
    )
    blobs_to_delete.append(upload_blob)

    with tempfile.NamedTemporaryFile() as tmp:
        download_blob = shared_bucket.get_blob(blob_name)

        for key, value in METADATA.items():
            assert getattr(download_blob, key) == value

        download_blob.download_to_file(tmp)
        tmp.seek(0)

        with open(source_file["path"], "rb") as sf:
            source_contents = sf.read()
            temp_contents = tmp.read()
            assert source_contents == temp_contents


def test_upload_chunks_concurrently_with_content_encoding(
    shared_bucket, file_data, blobs_to_delete
):
    import gzip

    METADATA = {
        "content_encoding": "gzip",
    }

    source_file = file_data["big"]
    filename = source_file["path"]
    blob_name = "mpu_file_encoded"
    upload_blob = shared_bucket.blob(blob_name)

    for key, value in METADATA.items():
        setattr(upload_blob, key, value)

    chunk_size = 5 * 1024 * 1024  # Minimum supported by XML MPU API

    with tempfile.NamedTemporaryFile() as tmp_gzip:
        with open(filename, "rb") as f:
            compressed_bytes = gzip.compress(f.read())

        tmp_gzip.write(compressed_bytes)
        tmp_gzip.seek(0)
        transfer_manager.upload_chunks_concurrently(
            tmp_gzip.name, upload_blob, chunk_size=chunk_size, deadline=DEADLINE
        )
        blobs_to_delete.append(upload_blob)

    with tempfile.NamedTemporaryFile() as tmp:
        download_blob = shared_bucket.get_blob(blob_name)

        for key, value in METADATA.items():
            assert getattr(download_blob, key) == value

        download_blob.download_to_file(tmp)
        tmp.seek(0)

        with open(source_file["path"], "rb") as sf:
            source_contents = sf.read()
            temp_contents = tmp.read()
            assert source_contents == temp_contents


def test_upload_chunks_concurrently_with_encryption_key(
    shared_bucket, file_data, blobs_to_delete
):
    source_file = file_data["big"]
    filename = source_file["path"]
    blob_name = "mpu_file_encrypted"
    upload_blob = shared_bucket.blob(blob_name, encryption_key=encryption_key)

    chunk_size = 5 * 1024 * 1024  # Minimum supported by XML MPU API
    assert os.path.getsize(filename) > chunk_size  # Won't make a good test otherwise

    transfer_manager.upload_chunks_concurrently(
        filename, upload_blob, chunk_size=chunk_size, deadline=DEADLINE
    )
    blobs_to_delete.append(upload_blob)

    with tempfile.NamedTemporaryFile() as tmp:
        download_blob = shared_bucket.get_blob(blob_name, encryption_key=encryption_key)

        download_blob.download_to_file(tmp)
        tmp.seek(0)

        with open(source_file["path"], "rb") as sf:
            source_contents = sf.read()
            temp_contents = tmp.read()
            assert source_contents == temp_contents

    with tempfile.NamedTemporaryFile() as tmp:
        keyless_blob = shared_bucket.get_blob(blob_name)

        with pytest.raises(exceptions.BadRequest):
            keyless_blob.download_to_file(tmp)


def test_upload_chunks_concurrently_with_kms(
    kms_bucket, file_data, blobs_to_delete, kms_key_name
):
    source_file = file_data["big"]
    filename = source_file["path"]
    blob_name = "mpu_file_kms"
    blob = kms_bucket.blob(blob_name, kms_key_name=kms_key_name)

    chunk_size = 5 * 1024 * 1024  # Minimum supported by XML MPU API
    assert os.path.getsize(filename) > chunk_size  # Won't make a good test otherwise

    transfer_manager.upload_chunks_concurrently(
        filename, blob, chunk_size=chunk_size, deadline=DEADLINE
    )
    blobs_to_delete.append(blob)
    blob.reload()
    assert blob.kms_key_name.startswith(kms_key_name)

    with tempfile.NamedTemporaryFile() as tmp:
        blob.download_to_file(tmp)
        tmp.seek(0)

        with open(source_file["path"], "rb") as sf:
            source_contents = sf.read()
            temp_contents = tmp.read()
            assert source_contents == temp_contents
