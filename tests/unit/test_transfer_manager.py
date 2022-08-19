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

from google.cloud.storage import transfer_manager

import tempfile
import unittest
import mock

class Test_Transfer_Manager(unittest.TestCase):
    @staticmethod
    def _make_client(*args, **kw):
        from google.cloud.storage.client import Client

        return mock.create_autospec(Client, instance=True, **kw)

    def test_upload_many_with_filenames(self):
        FILE_BLOB_PAIRS = [
            ("file_a.txt", mock.Mock()),
            ("file_b.txt", mock.Mock())
        ]
        FAKE_CONTENT_TYPE = "text/fake"
        UPLOAD_KWARGS = {"content-type": FAKE_CONTENT_TYPE}
        EXPECTED_UPLOAD_KWARGS = {"if_not_generation_match": 0, **UPLOAD_KWARGS}
        FAKE_RESULT = "nothing to see here"

        for _, blob_mock in FILE_BLOB_PAIRS:
            blob_mock.upload_from_filename.return_value = FAKE_RESULT

        results = transfer_manager.upload_many(
            FILE_BLOB_PAIRS,
            skip_if_exists=True,
            upload_kwargs=UPLOAD_KWARGS)
        for (filename, mock_blob) in FILE_BLOB_PAIRS:
            mock_blob.upload_from_filename.assert_any_call(filename, **EXPECTED_UPLOAD_KWARGS)
        for result in results:
            self.assertEqual(result, FAKE_RESULT)

    def test_upload_many_with_file_objs(self):
        FILE_BLOB_PAIRS = [
            (tempfile.TemporaryFile(), mock.Mock()),
            (tempfile.TemporaryFile(), mock.Mock())
        ]
        FAKE_CONTENT_TYPE = "text/fake"
        UPLOAD_KWARGS = {"content-type": FAKE_CONTENT_TYPE}
        EXPECTED_UPLOAD_KWARGS = {"if_not_generation_match": 0, **UPLOAD_KWARGS}
        FAKE_RESULT = "nothing to see here"

        for _, blob_mock in FILE_BLOB_PAIRS:
            blob_mock.upload_from_file.return_value = FAKE_RESULT

        results = transfer_manager.upload_many(
            FILE_BLOB_PAIRS,
            skip_if_exists=True,
            upload_kwargs=UPLOAD_KWARGS)
        for (file, mock_blob) in FILE_BLOB_PAIRS:
            mock_blob.upload_from_file.assert_any_call(file, **EXPECTED_UPLOAD_KWARGS)
        for result in results:
            self.assertEqual(result, FAKE_RESULT)

    def test_upload_many_passes_concurrency_options(self):
        FILE_BLOB_PAIRS = [
            (tempfile.TemporaryFile(), mock.Mock()),
            (tempfile.TemporaryFile(), mock.Mock())
        ]
        MAX_WORKERS = 7
        DEADLINE = 10
        with mock.patch("concurrent.futures.ThreadPoolExecutor") as pool_patch, mock.patch("concurrent.futures.wait") as wait_patch:
            transfer_manager.upload_many(
                FILE_BLOB_PAIRS,
                max_workers=MAX_WORKERS,
                deadline=DEADLINE)
            pool_patch.assert_called_with(max_workers=MAX_WORKERS)
            wait_patch.assert_called_with(mock.ANY, timeout=DEADLINE, return_when=mock.ANY)

    def test_upload_many_suppresses_exceptions(self):
        FILE_BLOB_PAIRS = [
            ("file_a.txt", mock.Mock()),
            ("file_b.txt", mock.Mock())
        ]
        for _, mock_blob in FILE_BLOB_PAIRS:
            mock_blob.upload_from_filename.side_effect = ConnectionError()

        results = transfer_manager.upload_many(FILE_BLOB_PAIRS)
        for result in results:
            self.assertEqual(type(result), ConnectionError)

    def test_upload_many_raises_exceptions(self):
        FILE_BLOB_PAIRS = [
            ("file_a.txt", mock.Mock()),
            ("file_b.txt", mock.Mock())
        ]
        for _, mock_blob in FILE_BLOB_PAIRS:
            mock_blob.upload_from_filename.side_effect = ConnectionError()

        with self.assertRaises(ConnectionError):
            transfer_manager.upload_many(
                FILE_BLOB_PAIRS,
                raise_exception=True)

    def test_download_many_with_filenames(self):
        BLOB_FILE_PAIRS = [
            (mock.Mock(), "file_a.txt"),
            (mock.Mock(), "file_b.txt")
        ]
        FAKE_ENCODING = "fake_gzip"
        DOWNLOAD_KWARGS = {"accept-encoding": FAKE_ENCODING}
        FAKE_RESULT = "nothing to see here"

        for blob_mock, _ in BLOB_FILE_PAIRS:
            blob_mock.download_to_filename.return_value = FAKE_RESULT

        results = transfer_manager.download_many(
            BLOB_FILE_PAIRS,
            download_kwargs=DOWNLOAD_KWARGS)
        for (mock_blob, file) in BLOB_FILE_PAIRS:
            mock_blob.download_to_filename.assert_any_call(file, **DOWNLOAD_KWARGS)
        for result in results:
            self.assertEqual(result, FAKE_RESULT)

    def test_download_many_with_file_objs(self):
        BLOB_FILE_PAIRS = [
            (mock.Mock(), tempfile.TemporaryFile()),
            (mock.Mock(), tempfile.TemporaryFile())
        ]
        FAKE_ENCODING = "fake_gzip"
        DOWNLOAD_KWARGS = {"accept-encoding": FAKE_ENCODING}
        FAKE_RESULT = "nothing to see here"

        for blob_mock, _ in BLOB_FILE_PAIRS:
            blob_mock.download_to_file.return_value = FAKE_RESULT

        results = transfer_manager.download_many(
            BLOB_FILE_PAIRS,
            download_kwargs=DOWNLOAD_KWARGS)
        for (mock_blob, file) in BLOB_FILE_PAIRS:
            mock_blob.download_to_file.assert_any_call(file, **DOWNLOAD_KWARGS)
        for result in results:
            self.assertEqual(result, FAKE_RESULT)

    def test_download_many_passes_concurrency_options(self):
        BLOB_FILE_PAIRS = [
            (mock.Mock(), tempfile.TemporaryFile()),
            (mock.Mock(), tempfile.TemporaryFile())
        ]
        MAX_WORKERS = 7
        DEADLINE = 10
        with mock.patch("concurrent.futures.ThreadPoolExecutor") as pool_patch, mock.patch("concurrent.futures.wait") as wait_patch:
            transfer_manager.download_many(
                BLOB_FILE_PAIRS,
                max_workers=MAX_WORKERS,
                deadline=DEADLINE)
            pool_patch.assert_called_with(max_workers=MAX_WORKERS)
            wait_patch.assert_called_with(mock.ANY, timeout=DEADLINE, return_when=mock.ANY)

    def test_download_many_suppresses_exceptions(self):
        BLOB_FILE_PAIRS = [
            (mock.Mock(), "file_a.txt"),
            (mock.Mock(), "file_b.txt")
        ]
        for mock_blob, _ in BLOB_FILE_PAIRS:
            mock_blob.download_from_filename.side_effect = ConnectionError()

        results = transfer_manager.download_many(BLOB_FILE_PAIRS)
        for result in results:
            self.assertEqual(type(result), ConnectionError)

    # def test_download_many_raises_exceptions(self):
    #     BLOB_FILE_PAIRS = [
    #         (mock.Mock(), "file_a.txt"),
    #         (mock.Mock(), "file_b.txt")
    #     ]
    #     for mock_blob, _ in BLOB_FILE_PAIRS:
    #         mock_blob.download_from_filename.side_effect = ConnectionError()

    #     results = transfer_manager.download_many(BLOB_FILE_PAIRS)
    #     for result in results:
    #         self.assertEqual(type(result), ConnectionError)

    #     with self.assertRaises(ConnectionError):
    #         transfer_manager.download_many(
    #             FILE_BLOB_PAIRS,
    #             raise_exception=True)
