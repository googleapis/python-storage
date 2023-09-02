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

import pytest

with pytest.warns(UserWarning):
    from google.cloud.storage import transfer_manager

from google.cloud.storage import Blob
from google.cloud.storage import Client

from google.api_core import exceptions

import os
import tempfile
import mock
import pickle

BLOB_TOKEN_STRING = "blob token"
FAKE_CONTENT_TYPE = "text/fake"
UPLOAD_KWARGS = {"content-type": FAKE_CONTENT_TYPE}
FAKE_RESULT = "nothing to see here"
FAKE_ENCODING = "fake_gzip"
DOWNLOAD_KWARGS = {"accept-encoding": FAKE_ENCODING}
CHUNK_SIZE = 8
HOSTNAME = "https://example.com/"
URL = "https://example.com/bucket/blob/"


# Used in subprocesses only, so excluded from coverage
def _validate_blob_token_in_subprocess(
    maybe_pickled_blob, method_name, path_or_file, **kwargs
):  # pragma: NO COVER
    assert pickle.loads(maybe_pickled_blob) == BLOB_TOKEN_STRING
    assert method_name.endswith("filename")
    assert path_or_file.startswith("file")
    assert kwargs == UPLOAD_KWARGS or kwargs == DOWNLOAD_KWARGS
    return FAKE_RESULT


def test_upload_many_with_filenames():
    FILE_BLOB_PAIRS = [
        ("file_a.txt", mock.Mock(spec=Blob)),
        ("file_b.txt", mock.Mock(spec=Blob)),
    ]
    EXPECTED_UPLOAD_KWARGS = {"if_generation_match": 0, **UPLOAD_KWARGS}

    for _, blob_mock in FILE_BLOB_PAIRS:
        blob_mock.upload_from_filename.return_value = FAKE_RESULT

    results = transfer_manager.upload_many(
        FILE_BLOB_PAIRS,
        skip_if_exists=True,
        upload_kwargs=UPLOAD_KWARGS,
        worker_type=transfer_manager.THREAD,
    )
    for (filename, mock_blob) in FILE_BLOB_PAIRS:
        mock_blob.upload_from_filename.assert_any_call(
            filename, **EXPECTED_UPLOAD_KWARGS
        )
    for result in results:
        assert result == FAKE_RESULT


def test_upload_many_with_file_objs():
    FILE_BLOB_PAIRS = [
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
    ]
    EXPECTED_UPLOAD_KWARGS = {"if_generation_match": 0, **UPLOAD_KWARGS}

    for _, blob_mock in FILE_BLOB_PAIRS:
        blob_mock.upload_from_file.return_value = FAKE_RESULT

    results = transfer_manager.upload_many(
        FILE_BLOB_PAIRS,
        skip_if_exists=True,
        upload_kwargs=UPLOAD_KWARGS,
        worker_type=transfer_manager.THREAD,
    )
    for (file, mock_blob) in FILE_BLOB_PAIRS:
        mock_blob.upload_from_file.assert_any_call(file, **EXPECTED_UPLOAD_KWARGS)
    for result in results:
        assert result == FAKE_RESULT


def test_upload_many_passes_concurrency_options():
    FILE_BLOB_PAIRS = [
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
    ]
    MAX_WORKERS = 7
    DEADLINE = 10
    with mock.patch("concurrent.futures.ThreadPoolExecutor") as pool_patch, mock.patch(
        "concurrent.futures.wait"
    ) as wait_patch:
        transfer_manager.upload_many(
            FILE_BLOB_PAIRS,
            deadline=DEADLINE,
            worker_type=transfer_manager.THREAD,
            max_workers=MAX_WORKERS,
        )
        pool_patch.assert_called_with(max_workers=MAX_WORKERS)
        wait_patch.assert_called_with(mock.ANY, timeout=DEADLINE, return_when=mock.ANY)


def test_threads_deprecation_with_upload():
    FILE_BLOB_PAIRS = [
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
    ]
    MAX_WORKERS = 7
    DEADLINE = 10
    with mock.patch("concurrent.futures.ThreadPoolExecutor") as pool_patch, mock.patch(
        "concurrent.futures.wait"
    ) as wait_patch:
        with pytest.warns():
            transfer_manager.upload_many(
                FILE_BLOB_PAIRS, deadline=DEADLINE, threads=MAX_WORKERS
            )
        pool_patch.assert_called_with(max_workers=MAX_WORKERS)
        wait_patch.assert_called_with(mock.ANY, timeout=DEADLINE, return_when=mock.ANY)


def test_threads_deprecation_conflict_with_upload():
    FILE_BLOB_PAIRS = [
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
        (tempfile.TemporaryFile(), mock.Mock(spec=Blob)),
    ]
    MAX_WORKERS = 7
    DEADLINE = 10
    with pytest.raises(ValueError):
        transfer_manager.upload_many(
            FILE_BLOB_PAIRS,
            deadline=DEADLINE,
            threads=5,
            worker_type=transfer_manager.THREAD,
            max_workers=MAX_WORKERS,
        )


def test_upload_many_suppresses_exceptions():
    FILE_BLOB_PAIRS = [
        ("file_a.txt", mock.Mock(spec=Blob)),
        ("file_b.txt", mock.Mock(spec=Blob)),
    ]
    for _, mock_blob in FILE_BLOB_PAIRS:
        mock_blob.upload_from_filename.side_effect = ConnectionError()

    results = transfer_manager.upload_many(
        FILE_BLOB_PAIRS, worker_type=transfer_manager.THREAD
    )
    for result in results:
        assert isinstance(result, ConnectionError)


def test_upload_many_raises_exceptions():
    FILE_BLOB_PAIRS = [
        ("file_a.txt", mock.Mock(spec=Blob)),
        ("file_b.txt", mock.Mock(spec=Blob)),
    ]
    for _, mock_blob in FILE_BLOB_PAIRS:
        mock_blob.upload_from_filename.side_effect = ConnectionError()

    with pytest.raises(ConnectionError):
        transfer_manager.upload_many(
            FILE_BLOB_PAIRS, raise_exception=True, worker_type=transfer_manager.THREAD
        )


def test_upload_many_suppresses_412_with_skip_if_exists():
    FILE_BLOB_PAIRS = [
        ("file_a.txt", mock.Mock(spec=Blob)),
        ("file_b.txt", mock.Mock(spec=Blob)),
    ]
    for _, mock_blob in FILE_BLOB_PAIRS:
        mock_blob.upload_from_filename.side_effect = exceptions.PreconditionFailed(
            "412"
        )
    results = transfer_manager.upload_many(
        FILE_BLOB_PAIRS,
        skip_if_exists=True,
        raise_exception=True,
        worker_type=transfer_manager.THREAD,
    )
    for result in results:
        assert isinstance(result, exceptions.PreconditionFailed)


def test_upload_many_with_processes():
    # Mocks are not pickleable, so we send token strings over the wire.
    FILE_BLOB_PAIRS = [
        ("file_a.txt", BLOB_TOKEN_STRING),
        ("file_b.txt", BLOB_TOKEN_STRING),
    ]

    with mock.patch(
        "google.cloud.storage.transfer_manager._call_method_on_maybe_pickled_blob",
        new=_validate_blob_token_in_subprocess,
    ):
        results = transfer_manager.upload_many(
            FILE_BLOB_PAIRS,
            upload_kwargs=UPLOAD_KWARGS,
            worker_type=transfer_manager.PROCESS,
            raise_exception=True,
        )
    for result in results:
        assert result == FAKE_RESULT


def test_upload_many_with_processes_rejects_file_obj():
    # Mocks are not pickleable, so we send token strings over the wire.
    FILE_BLOB_PAIRS = [
        ("file_a.txt", BLOB_TOKEN_STRING),
        (tempfile.TemporaryFile(), BLOB_TOKEN_STRING),
    ]

    with mock.patch(
        "google.cloud.storage.transfer_manager._call_method_on_maybe_pickled_blob",
        new=_validate_blob_token_in_subprocess,
    ):
        with pytest.raises(ValueError):
            transfer_manager.upload_many(
                FILE_BLOB_PAIRS,
                upload_kwargs=UPLOAD_KWARGS,
                worker_type=transfer_manager.PROCESS,
            )


def test_download_many_with_filenames():
    BLOB_FILE_PAIRS = [
        (mock.Mock(spec=Blob), "file_a.txt"),
        (mock.Mock(spec=Blob), "file_b.txt"),
    ]

    for blob_mock, _ in BLOB_FILE_PAIRS:
        blob_mock.download_to_filename.return_value = FAKE_RESULT

    results = transfer_manager.download_many(
        BLOB_FILE_PAIRS,
        download_kwargs=DOWNLOAD_KWARGS,
        worker_type=transfer_manager.THREAD,
    )
    for (mock_blob, file) in BLOB_FILE_PAIRS:
        mock_blob.download_to_filename.assert_any_call(file, **DOWNLOAD_KWARGS)
    for result in results:
        assert result == FAKE_RESULT


def test_download_many_with_file_objs():
    BLOB_FILE_PAIRS = [
        (mock.Mock(spec=Blob), tempfile.TemporaryFile()),
        (mock.Mock(spec=Blob), tempfile.TemporaryFile()),
    ]

    for blob_mock, _ in BLOB_FILE_PAIRS:
        blob_mock.download_to_file.return_value = FAKE_RESULT

    results = transfer_manager.download_many(
        BLOB_FILE_PAIRS,
        download_kwargs=DOWNLOAD_KWARGS,
        worker_type=transfer_manager.THREAD,
    )
    for (mock_blob, file) in BLOB_FILE_PAIRS:
        mock_blob.download_to_file.assert_any_call(file, **DOWNLOAD_KWARGS)
    for result in results:
        assert result == FAKE_RESULT


def test_download_many_passes_concurrency_options():
    BLOB_FILE_PAIRS = [
        (mock.Mock(spec=Blob), tempfile.TemporaryFile()),
        (mock.Mock(spec=Blob), tempfile.TemporaryFile()),
    ]
    MAX_WORKERS = 7
    DEADLINE = 10
    with mock.patch("concurrent.futures.ThreadPoolExecutor") as pool_patch, mock.patch(
        "concurrent.futures.wait"
    ) as wait_patch:
        transfer_manager.download_many(
            BLOB_FILE_PAIRS,
            deadline=DEADLINE,
            worker_type=transfer_manager.THREAD,
            max_workers=MAX_WORKERS,
        )
        pool_patch.assert_called_with(max_workers=MAX_WORKERS)
        wait_patch.assert_called_with(mock.ANY, timeout=DEADLINE, return_when=mock.ANY)


def test_download_many_suppresses_exceptions():
    BLOB_FILE_PAIRS = [
        (mock.Mock(spec=Blob), "file_a.txt"),
        (mock.Mock(spec=Blob), "file_b.txt"),
    ]
    for mock_blob, _ in BLOB_FILE_PAIRS:
        mock_blob.download_to_filename.side_effect = ConnectionError()

    results = transfer_manager.download_many(
        BLOB_FILE_PAIRS, worker_type=transfer_manager.THREAD
    )
    for result in results:
        assert isinstance(result, ConnectionError)


def test_download_many_raises_exceptions():
    BLOB_FILE_PAIRS = [
        (mock.Mock(spec=Blob), "file_a.txt"),
        (mock.Mock(spec=Blob), "file_b.txt"),
    ]
    for mock_blob, _ in BLOB_FILE_PAIRS:
        mock_blob.download_to_filename.side_effect = ConnectionError()

    with pytest.raises(ConnectionError):
        transfer_manager.download_many(
            BLOB_FILE_PAIRS, raise_exception=True, worker_type=transfer_manager.THREAD
        )


def test_download_many_with_processes():
    # Mocks are not pickleable, so we send token strings over the wire.
    BLOB_FILE_PAIRS = [
        (BLOB_TOKEN_STRING, "file_a.txt"),
        (BLOB_TOKEN_STRING, "file_b.txt"),
    ]

    with mock.patch(
        "google.cloud.storage.transfer_manager._call_method_on_maybe_pickled_blob",
        new=_validate_blob_token_in_subprocess,
    ):
        results = transfer_manager.download_many(
            BLOB_FILE_PAIRS,
            download_kwargs=DOWNLOAD_KWARGS,
            worker_type=transfer_manager.PROCESS,
        )
    for result in results:
        assert result == FAKE_RESULT


def test_download_many_with_processes_rejects_file_obj():
    # Mocks are not pickleable, so we send token strings over the wire.
    BLOB_FILE_PAIRS = [
        (BLOB_TOKEN_STRING, "file_a.txt"),
        (BLOB_TOKEN_STRING, tempfile.TemporaryFile()),
    ]

    with mock.patch(
        "google.cloud.storage.transfer_manager._call_method_on_maybe_pickled_blob",
        new=_validate_blob_token_in_subprocess,
    ):
        with pytest.raises(ValueError):
            transfer_manager.download_many(
                BLOB_FILE_PAIRS,
                download_kwargs=DOWNLOAD_KWARGS,
                worker_type=transfer_manager.PROCESS,
            )


def test_upload_many_from_filenames():
    bucket = mock.Mock()

    FILENAMES = ["file_a.txt", "file_b.txt"]
    ROOT = "mypath/"
    PREFIX = "myprefix/"
    KEY_NAME = "keyname"
    BLOB_CONSTRUCTOR_KWARGS = {"kms_key_name": KEY_NAME}
    UPLOAD_KWARGS = {"content-type": "text/fake"}
    MAX_WORKERS = 7
    DEADLINE = 10
    WORKER_TYPE = transfer_manager.THREAD

    EXPECTED_FILE_BLOB_PAIRS = [
        (os.path.join(ROOT, filename), mock.ANY) for filename in FILENAMES
    ]

    with mock.patch(
        "google.cloud.storage.transfer_manager.upload_many"
    ) as mock_upload_many:
        transfer_manager.upload_many_from_filenames(
            bucket,
            FILENAMES,
            source_directory=ROOT,
            blob_name_prefix=PREFIX,
            skip_if_exists=True,
            blob_constructor_kwargs=BLOB_CONSTRUCTOR_KWARGS,
            upload_kwargs=UPLOAD_KWARGS,
            deadline=DEADLINE,
            raise_exception=True,
            worker_type=WORKER_TYPE,
            max_workers=MAX_WORKERS,
        )

    mock_upload_many.assert_called_once_with(
        EXPECTED_FILE_BLOB_PAIRS,
        skip_if_exists=True,
        upload_kwargs=UPLOAD_KWARGS,
        deadline=DEADLINE,
        raise_exception=True,
        worker_type=WORKER_TYPE,
        max_workers=MAX_WORKERS,
    )
    bucket.blob.assert_any_call(PREFIX + FILENAMES[0], **BLOB_CONSTRUCTOR_KWARGS)
    bucket.blob.assert_any_call(PREFIX + FILENAMES[1], **BLOB_CONSTRUCTOR_KWARGS)


def test_upload_many_from_filenames_minimal_args():
    bucket = mock.Mock()

    FILENAMES = ["file_a.txt", "file_b.txt"]

    EXPECTED_FILE_BLOB_PAIRS = [(filename, mock.ANY) for filename in FILENAMES]

    with mock.patch(
        "google.cloud.storage.transfer_manager.upload_many"
    ) as mock_upload_many:
        transfer_manager.upload_many_from_filenames(
            bucket,
            FILENAMES,
        )

    mock_upload_many.assert_called_once_with(
        EXPECTED_FILE_BLOB_PAIRS,
        skip_if_exists=False,
        upload_kwargs=None,
        deadline=None,
        raise_exception=False,
        worker_type=transfer_manager.PROCESS,
        max_workers=8,
    )
    bucket.blob.assert_any_call(FILENAMES[0])
    bucket.blob.assert_any_call(FILENAMES[1])


def test_download_many_to_path():
    bucket = mock.Mock()

    BLOBNAMES = ["file_a.txt", "file_b.txt", "dir_a/file_c.txt"]
    PATH_ROOT = "mypath/"
    BLOB_NAME_PREFIX = "myprefix/"
    DOWNLOAD_KWARGS = {"accept-encoding": "fake-gzip"}
    MAX_WORKERS = 7
    DEADLINE = 10
    WORKER_TYPE = transfer_manager.THREAD

    EXPECTED_BLOB_FILE_PAIRS = [
        (mock.ANY, os.path.join(PATH_ROOT, blobname)) for blobname in BLOBNAMES
    ]

    with mock.patch(
        "google.cloud.storage.transfer_manager.download_many"
    ) as mock_download_many:
        transfer_manager.download_many_to_path(
            bucket,
            BLOBNAMES,
            destination_directory=PATH_ROOT,
            blob_name_prefix=BLOB_NAME_PREFIX,
            download_kwargs=DOWNLOAD_KWARGS,
            deadline=DEADLINE,
            create_directories=False,
            raise_exception=True,
            max_workers=MAX_WORKERS,
            worker_type=WORKER_TYPE,
        )

    mock_download_many.assert_called_once_with(
        EXPECTED_BLOB_FILE_PAIRS,
        download_kwargs=DOWNLOAD_KWARGS,
        deadline=DEADLINE,
        raise_exception=True,
        max_workers=MAX_WORKERS,
        worker_type=WORKER_TYPE,
    )
    for blobname in BLOBNAMES:
        bucket.blob.assert_any_call(BLOB_NAME_PREFIX + blobname)


def test_download_many_to_path_creates_directories():
    bucket = mock.Mock()

    with tempfile.TemporaryDirectory() as tempdir:
        DIR_NAME = "dir_a/dir_b"
        BLOBNAMES = [
            "file_a.txt",
            "file_b.txt",
            os.path.join(DIR_NAME, "file_c.txt"),
        ]

        EXPECTED_BLOB_FILE_PAIRS = [
            (mock.ANY, os.path.join(tempdir, blobname)) for blobname in BLOBNAMES
        ]

        with mock.patch(
            "google.cloud.storage.transfer_manager.download_many"
        ) as mock_download_many:
            transfer_manager.download_many_to_path(
                bucket,
                BLOBNAMES,
                destination_directory=tempdir,
                create_directories=True,
                raise_exception=True,
            )

        mock_download_many.assert_called_once_with(
            EXPECTED_BLOB_FILE_PAIRS,
            download_kwargs=None,
            deadline=None,
            raise_exception=True,
            worker_type=transfer_manager.PROCESS,
            max_workers=8,
        )
        for blobname in BLOBNAMES:
            bucket.blob.assert_any_call(blobname)

        assert os.path.isdir(os.path.join(tempdir, DIR_NAME))


def test_download_chunks_concurrently():
    blob_mock = mock.Mock(spec=Blob)
    FILENAME = "file_a.txt"
    MULTIPLE = 4
    blob_mock.size = CHUNK_SIZE * MULTIPLE

    blob_mock.download_to_filename.return_value = FAKE_RESULT

    with mock.patch("__main__.open", mock.mock_open()):
        result = transfer_manager.download_chunks_concurrently(
            blob_mock,
            FILENAME,
            chunk_size=CHUNK_SIZE,
            download_kwargs=DOWNLOAD_KWARGS,
            worker_type=transfer_manager.THREAD,
        )
    for x in range(MULTIPLE):
        blob_mock.download_to_file.assert_any_call(
            mock.ANY,
            **DOWNLOAD_KWARGS,
            start=x * CHUNK_SIZE,
            end=((x + 1) * CHUNK_SIZE) - 1
        )
    assert blob_mock.download_to_file.call_count == 4
    assert result is None


def test_download_chunks_concurrently_raises_on_start_and_end():
    blob_mock = mock.Mock(spec=Blob)
    FILENAME = "file_a.txt"
    MULTIPLE = 4
    blob_mock.size = CHUNK_SIZE * MULTIPLE

    with mock.patch("__main__.open", mock.mock_open()):
        with pytest.raises(ValueError):
            transfer_manager.download_chunks_concurrently(
                blob_mock,
                FILENAME,
                chunk_size=CHUNK_SIZE,
                worker_type=transfer_manager.THREAD,
                download_kwargs={
                    "start": CHUNK_SIZE,
                },
            )
        with pytest.raises(ValueError):
            transfer_manager.download_chunks_concurrently(
                blob_mock,
                FILENAME,
                chunk_size=CHUNK_SIZE,
                worker_type=transfer_manager.THREAD,
                download_kwargs={
                    "end": (CHUNK_SIZE * (MULTIPLE - 1)) - 1,
                },
            )


def test_download_chunks_concurrently_passes_concurrency_options():
    blob_mock = mock.Mock(spec=Blob)
    FILENAME = "file_a.txt"
    MAX_WORKERS = 7
    DEADLINE = 10
    MULTIPLE = 4
    blob_mock.size = CHUNK_SIZE * MULTIPLE

    with mock.patch("concurrent.futures.ThreadPoolExecutor") as pool_patch, mock.patch(
        "concurrent.futures.wait"
    ) as wait_patch, mock.patch("__main__.open", mock.mock_open()):
        transfer_manager.download_chunks_concurrently(
            blob_mock,
            FILENAME,
            chunk_size=CHUNK_SIZE,
            deadline=DEADLINE,
            worker_type=transfer_manager.THREAD,
            max_workers=MAX_WORKERS,
        )
        pool_patch.assert_called_with(max_workers=MAX_WORKERS)
        wait_patch.assert_called_with(mock.ANY, timeout=DEADLINE, return_when=mock.ANY)


def test_upload_chunks_concurrently():
    blob_mock = mock.Mock()
    blob_mock.name = "blob"
    blob_mock.bucket.name = "bucket"
    transport = mock.Mock()
    blob_mock._get_transport = mock.Mock(return_value=transport)
    blob_mock._get_content_type = mock.Mock(return_value=FAKE_CONTENT_TYPE)
    blob_mock.client = _PickleableMockClient(identify_as_client=True)
    FILENAME = "file_a.txt"
    SIZE = 2048

    container_mock = mock.Mock()
    container_mock.upload_id = "abcd"
    part_mock = mock.Mock()
    ETAG = "efgh"
    part_mock.etag = ETAG

    with mock.patch("os.path.getsize", return_value=SIZE), mock.patch(
        "google.cloud.storage.transfer_manager.XMLMPUContainer",
        return_value=container_mock,
    ), mock.patch(
        "google.cloud.storage.transfer_manager.XMLMPUPart", return_value=part_mock
    ):
        transfer_manager.upload_chunks_concurrently(
            FILENAME,
            blob_mock,
            chunk_size=SIZE // 2,
            worker_type=transfer_manager.THREAD,
        )
        container_mock.initiate.assert_called_once_with(
            transport=transport, content_type=FAKE_CONTENT_TYPE
        )
        container_mock.register_part.assert_any_call(1, ETAG)
        container_mock.register_part.assert_any_call(2, ETAG)
        container_mock.finalize.assert_called_once_with(transport)
        part_mock.upload.assert_called_with(blob_mock.client._http)


def test_upload_chunks_concurrently_passes_concurrency_options():
    blob_mock = mock.Mock()
    blob_mock.name = "blob"
    blob_mock.bucket.name = "bucket"
    transport = mock.Mock()
    blob_mock._get_transport = mock.Mock(return_value=transport)
    blob_mock._get_content_type = mock.Mock(return_value=FAKE_CONTENT_TYPE)
    blob_mock.client = _PickleableMockClient(identify_as_client=True)
    FILENAME = "file_a.txt"
    SIZE = 2048

    container_mock = mock.Mock()
    container_mock.upload_id = "abcd"

    MAX_WORKERS = 7
    DEADLINE = 10

    with mock.patch("os.path.getsize", return_value=SIZE), mock.patch(
        "google.cloud.storage.transfer_manager.XMLMPUContainer",
        return_value=container_mock,
    ), mock.patch("concurrent.futures.ThreadPoolExecutor") as pool_patch, mock.patch(
        "concurrent.futures.wait"
    ) as wait_patch:
        try:
            transfer_manager.upload_chunks_concurrently(
                FILENAME,
                blob_mock,
                chunk_size=SIZE // 2,
                worker_type=transfer_manager.THREAD,
                max_workers=MAX_WORKERS,
                deadline=DEADLINE,
            )
        except ValueError:
            pass  # The futures don't actually work, so we expect this to abort.
            # Conveniently, that gives us a chance to test the auto-delete
            # exception handling feature.
        container_mock.cancel.assert_called_once_with(transport)
        pool_patch.assert_called_with(max_workers=MAX_WORKERS)
        wait_patch.assert_called_with(mock.ANY, timeout=DEADLINE, return_when=mock.ANY)


class _PickleableMockBlob:
    def __init__(
        self,
        name="",
        size=None,
        generation=None,
        size_after_reload=None,
        generation_after_reload=None,
    ):
        self.name = name
        self.size = size
        self.generation = generation
        self._size_after_reload = size_after_reload
        self._generation_after_reload = generation_after_reload

    def reload(self):
        self.size = self._size_after_reload
        self.generation = self._generation_after_reload

    def download_to_file(self, *args, **kwargs):
        return "SUCCESS"


class _PickleableMockConnection:
    @staticmethod
    def get_api_base_url_for_mtls():
        return HOSTNAME


class _PickleableMockClient:
    def __init__(self, identify_as_client=False):
        self._http = None
        self._connection = _PickleableMockConnection()
        self.identify_as_client = identify_as_client

    @property
    def __class__(self):
        if self.identify_as_client:
            return Client
        else:
            return _PickleableMockClient


# Used in subprocesses only, so excluded from coverage
def _validate_blob_token_in_subprocess_for_chunk(
    maybe_pickled_blob, filename, **kwargs
):  # pragma: NO COVER
    blob = pickle.loads(maybe_pickled_blob)
    assert isinstance(blob, _PickleableMockBlob)
    assert filename.startswith("file")
    return FAKE_RESULT


def test_download_chunks_concurrently_with_processes():
    blob = _PickleableMockBlob(
        "file_a_blob", size_after_reload=24, generation_after_reload=100
    )
    FILENAME = "file_a.txt"

    with mock.patch(
        "google.cloud.storage.transfer_manager._download_and_write_chunk_in_place",
        new=_validate_blob_token_in_subprocess_for_chunk,
    ), mock.patch("__main__.open", mock.mock_open()):
        result = transfer_manager.download_chunks_concurrently(
            blob,
            FILENAME,
            chunk_size=CHUNK_SIZE,
            download_kwargs=DOWNLOAD_KWARGS,
            worker_type=transfer_manager.PROCESS,
        )
    assert result is None


def test__LazyClient():
    fake_cache = {}
    MOCK_ID = 9999
    with mock.patch(
        "google.cloud.storage.transfer_manager._cached_clients", new=fake_cache
    ), mock.patch("google.cloud.storage.transfer_manager.Client"):
        lazyclient = transfer_manager._LazyClient(MOCK_ID)
        lazyclient_cached = transfer_manager._LazyClient(MOCK_ID)
        assert lazyclient is lazyclient_cached
        assert len(fake_cache) == 1


def test__pickle_client():
    # This test nominally has coverage, but doesn't assert that the essential
    # copyreg behavior in _pickle_client works. Unfortunately there doesn't seem
    # to be a good way to check that without actually creating a Client, which
    # will spin up HTTP connections undesirably. This is more fully checked in
    # the system tests.
    pkl = transfer_manager._pickle_client(FAKE_RESULT)
    assert pickle.loads(pkl) == FAKE_RESULT


def test__download_and_write_chunk_in_place():
    pickled_mock = pickle.dumps(_PickleableMockBlob())
    FILENAME = "file_a.txt"
    with mock.patch("__main__.open", mock.mock_open()):
        result = transfer_manager._download_and_write_chunk_in_place(
            pickled_mock, FILENAME, 0, 8, {}
        )
    assert result == "SUCCESS"


def test__upload_part():
    pickled_mock = pickle.dumps(_PickleableMockClient())
    FILENAME = "file_a.txt"
    UPLOAD_ID = "abcd"
    ETAG = "efgh"

    part = mock.Mock()
    part.etag = ETAG
    with mock.patch(
        "google.cloud.storage.transfer_manager.XMLMPUPart", return_value=part
    ):
        result = transfer_manager._upload_part(
            pickled_mock, URL, UPLOAD_ID, FILENAME, 0, 256, 1, None
        )
        part.upload.assert_called_once()
        assert result == (1, ETAG)


def test__get_pool_class_and_requirements_error():
    with pytest.raises(ValueError):
        transfer_manager._get_pool_class_and_requirements("garbage")


def test__reduce_client():
    fake_cache = {}
    client = mock.Mock()

    with mock.patch(
        "google.cloud.storage.transfer_manager._cached_clients", new=fake_cache
    ), mock.patch("google.cloud.storage.transfer_manager.Client"):
        transfer_manager._reduce_client(client)


def test__call_method_on_maybe_pickled_blob():
    blob = mock.Mock(spec=Blob)
    blob.download_to_file.return_value = "SUCCESS"
    result = transfer_manager._call_method_on_maybe_pickled_blob(
        blob, "download_to_file"
    )
    assert result == "SUCCESS"

    pickled_blob = pickle.dumps(_PickleableMockBlob())
    result = transfer_manager._call_method_on_maybe_pickled_blob(
        pickled_blob, "download_to_file"
    )
    assert result == "SUCCESS"
