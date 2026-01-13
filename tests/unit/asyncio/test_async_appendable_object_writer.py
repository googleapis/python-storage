# Copyright 2025 Google LLC
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

import io
import unittest
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock
import pytest

from google.api_core import exceptions
from google.rpc import status_pb2
from google.cloud._storage_v2.types import storage as storage_type
from google.cloud._storage_v2.types.storage import BidiWriteObjectRedirectedError
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
    _is_write_retryable,
    _MAX_CHUNK_SIZE_BYTES,
    _DEFAULT_FLUSH_INTERVAL_BYTES,
)

# Constants
BUCKET = "test-bucket"
OBJECT = "test-object"
GENERATION = 123
WRITE_HANDLE = b"test-write-handle"
PERSISTED_SIZE = 456
EIGHT_MIB = 8 * 1024 * 1024


class TestIsWriteRetryable(unittest.TestCase):
    """Exhaustive tests for retry predicate logic."""

    def test_standard_transient_errors(self):
        for exc in [
            exceptions.InternalServerError("500"),
            exceptions.ServiceUnavailable("503"),
            exceptions.DeadlineExceeded("timeout"),
            exceptions.TooManyRequests("429"),
        ]:
            self.assertTrue(_is_write_retryable(exc))

    def test_aborted_with_redirect_proto(self):
        # Direct redirect error wrapped in Aborted
        redirect = BidiWriteObjectRedirectedError(routing_token="token")
        exc = exceptions.Aborted("aborted", errors=[redirect])
        self.assertTrue(_is_write_retryable(exc))

    def test_aborted_with_trailers(self):
        # Setup Status with Redirect Detail
        status = status_pb2.Status()
        detail = status.details.add()
        detail.type_url = "type.googleapis.com/google.storage.v2.BidiWriteObjectRedirectedError"

        # Mock error with trailing_metadata method
        mock_grpc_error = MagicMock()
        mock_grpc_error.trailing_metadata.return_value = [
            ("grpc-status-details-bin", status.SerializeToString())
        ]

        # Aborted wraps the grpc error
        exc = exceptions.Aborted("aborted", errors=[mock_grpc_error])
        self.assertTrue(_is_write_retryable(exc))

    def test_aborted_without_metadata(self):
        mock_grpc_error = MagicMock()
        mock_grpc_error.trailing_metadata.return_value = []
        exc = exceptions.Aborted("bare aborted", errors=[mock_grpc_error])
        self.assertFalse(_is_write_retryable(exc))

    def test_non_retryable_errors(self):
        self.assertFalse(_is_write_retryable(exceptions.BadRequest("400")))
        self.assertFalse(_is_write_retryable(exceptions.NotFound("404")))


class TestAsyncAppendableObjectWriter(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_client = mock.AsyncMock()
        # Internal stream class patch
        self.mock_stream_patcher = mock.patch(
            "google.cloud.storage._experimental.asyncio.async_appendable_object_writer._AsyncWriteObjectStream"
        )
        self.mock_stream_cls = self.mock_stream_patcher.start()
        self.mock_stream = self.mock_stream_cls.return_value

        # Configure all async methods explicitly
        self.mock_stream.open = AsyncMock()
        self.mock_stream.close = AsyncMock()
        self.mock_stream.send = AsyncMock()
        self.mock_stream.recv = AsyncMock()

        # Default mock properties
        self.mock_stream.is_stream_open = False
        self.mock_stream.persisted_size = 0
        self.mock_stream.generation_number = GENERATION
        self.mock_stream.write_handle = WRITE_HANDLE

    def tearDown(self):
        self.mock_stream_patcher.stop()

    def _make_one(self, **kwargs):
        return AsyncAppendableObjectWriter(
            self.mock_client, BUCKET, OBJECT, **kwargs
        )

    # -------------------------------------------------------------------------
    # Initialization & Configuration Tests
    # -------------------------------------------------------------------------

    def test_init_defaults(self):
        writer = self._make_one()
        self.assertEqual(writer.bucket_name, BUCKET)
        self.assertEqual(writer.object_name, OBJECT)
        self.assertIsNone(writer.persisted_size)
        self.assertEqual(writer.bytes_appended_since_last_flush, 0)
        self.assertEqual(writer.flush_interval, _DEFAULT_FLUSH_INTERVAL_BYTES)

    def test_init_with_writer_options(self):
        writer = self._make_one(writer_options={"FLUSH_INTERVAL_BYTES": EIGHT_MIB})
        self.assertEqual(writer.flush_interval, EIGHT_MIB)

    def test_init_validation_chunk_size_raises(self):
        with self.assertRaises(exceptions.OutOfRange):
            self._make_one(writer_options={"FLUSH_INTERVAL_BYTES": _MAX_CHUNK_SIZE_BYTES - 1})

    def test_init_validation_multiple_raises(self):
        with self.assertRaises(exceptions.OutOfRange):
            self._make_one(writer_options={"FLUSH_INTERVAL_BYTES": _MAX_CHUNK_SIZE_BYTES + 1})

    def test_init_raises_if_crc32c_missing(self):
        with mock.patch("google.cloud.storage._experimental.asyncio._utils.google_crc32c") as mock_crc:
            mock_crc.implementation = "python"
            with self.assertRaises(exceptions.FailedPrecondition):
                self._make_one()

    # -------------------------------------------------------------------------
    # Stream Lifecycle Tests
    # -------------------------------------------------------------------------

    async def test_state_lookup_success(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream

        self.mock_stream.recv.return_value = storage_type.BidiWriteObjectResponse(persisted_size=100)

        size = await writer.state_lookup()

        self.mock_stream.send.assert_awaited_once()
        self.assertEqual(size, 100)
        self.assertEqual(writer.persisted_size, 100)

    async def test_state_lookup_raises_if_not_open(self):
        writer = self._make_one()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await writer.state_lookup()

    async def test_open_success(self):
        writer = self._make_one()
        self.mock_stream.generation_number = 456
        self.mock_stream.write_handle = b"new-h"
        self.mock_stream.persisted_size = 0

        await writer.open()

        self.assertTrue(writer._is_stream_open)
        self.assertEqual(writer.generation, 456)
        self.assertEqual(writer.write_handle, b"new-h")
        self.mock_stream.open.assert_awaited_once()

    async def test_open_already_open_raises(self):
        writer = self._make_one()
        writer._is_stream_open = True
        with self.assertRaisesRegex(ValueError, "already open"):
            await writer.open()

    def test_on_open_error_redirection(self):
        """Verify redirect info is extracted from helper."""
        writer = self._make_one()
        redirect = BidiWriteObjectRedirectedError(
            routing_token="rt1",
            write_handle=storage_type.BidiWriteHandle(handle=b"h1"),
            generation=777
        )

        with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._extract_bidi_writes_redirect_proto", return_value=redirect):
            writer._on_open_error(exceptions.Aborted("redirect"))

        self.assertEqual(writer._routing_token, "rt1")
        self.assertEqual(writer.write_handle.handle, b"h1")
        self.assertEqual(writer.generation, 777)

    # -------------------------------------------------------------------------
    # Append & Integration Tests
    # -------------------------------------------------------------------------

    async def test_append_integration_basic(self):
        """Verify append orchestrates manager and drives the internal generator."""
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.persisted_size = 0

        data = b"test-data"

        with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
            async def mock_execute(state, policy):
                factory = MockManager.call_args[0][1]
                dummy_reqs = [storage_type.BidiWriteObjectRequest()]
                gen = factory(dummy_reqs, state)

                self.mock_stream.recv.side_effect = [
                    storage_type.BidiWriteObjectResponse(
                        persisted_size=len(data),
                        write_handle=storage_type.BidiWriteHandle(handle=b"h2")
                    ),
                    None
                ]
                async for _ in gen: pass

            MockManager.return_value.execute.side_effect = mock_execute
            await writer.append(data)

            self.assertEqual(writer.persisted_size, len(data))
            sent_req = self.mock_stream.send.call_args[0][0]
            self.assertTrue(sent_req.state_lookup)
            self.assertTrue(sent_req.flush)

    async def test_append_recovery_reopens_stream(self):
        """Verifies re-opening logic on retry."""
        writer = self._make_one(write_handle=b"h1")
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        # Setup mock to allow close() call
        self.mock_stream.is_stream_open = True

        async def mock_open(metadata=None):
            writer.write_obj_stream = self.mock_stream
            writer._is_stream_open = True
            writer.persisted_size = 5
            writer.write_handle = b"h_recovered"

        with mock.patch.object(writer, "open", side_effect=mock_open) as mock_writer_open:
            with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
                async def mock_execute(state, policy):
                    factory = MockManager.call_args[0][1]
                    # Simulate Attempt 1 fail
                    gen1 = factory([], state)
                    try: await gen1.__anext__()
                    except: pass
                    # Simulate Attempt 2
                    gen2 = factory([], state)
                    self.mock_stream.recv.return_value = None
                    async for _ in gen2: pass

                MockManager.return_value.execute.side_effect = mock_execute
                await writer.append(b"0123456789")

                self.mock_stream.close.assert_awaited()
                mock_writer_open.assert_awaited()
                self.assertEqual(writer.persisted_size, 5)

    async def test_append_unimplemented_string_raises(self):
        writer = self._make_one()
        with self.assertRaises(NotImplementedError):
            await writer.append_from_string("test")

    # -------------------------------------------------------------------------
    # Flush, Close, Finalize
    # -------------------------------------------------------------------------

    async def test_flush_resets_counters(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.bytes_appended_since_last_flush = 100

        self.mock_stream.recv.return_value = storage_type.BidiWriteObjectResponse(persisted_size=200)

        await writer.flush()

        self.assertEqual(writer.bytes_appended_since_last_flush, 0)
        self.assertEqual(writer.persisted_size, 200)

    async def test_simple_flush(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.bytes_appended_since_last_flush = 50

        await writer.simple_flush()

        self.mock_stream.send.assert_awaited_with(storage_type.BidiWriteObjectRequest(flush=True))
        self.assertEqual(writer.bytes_appended_since_last_flush, 0)

    async def test_close_without_finalize(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.persisted_size = 50

        size = await writer.close()

        self.mock_stream.close.assert_awaited()
        self.assertFalse(writer._is_stream_open)
        self.assertEqual(size, 50)

    async def test_finalize_lifecycle(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream

        resource = storage_type.Object(size=999)
        self.mock_stream.recv.return_value = storage_type.BidiWriteObjectResponse(resource=resource)

        res = await writer.finalize()

        self.assertEqual(res, resource)
        self.assertEqual(writer.persisted_size, 999)
        self.mock_stream.send.assert_awaited_with(storage_type.BidiWriteObjectRequest(finish_write=True))
        self.mock_stream.close.assert_awaited()
        self.assertFalse(writer._is_stream_open)

    async def test_close_with_finalize_on_close(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.finalize = AsyncMock()

        await writer.close(finalize_on_close=True)
        writer.finalize.assert_awaited_once()

    # -------------------------------------------------------------------------
    # Helper Integration Tests
    # -------------------------------------------------------------------------

    async def test_append_from_file_integration(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.append = AsyncMock()

        fp = io.BytesIO(b"a" * 12)
        await writer.append_from_file(fp, block_size=4)

        self.assertEqual(writer.append.await_count, 3)

    async def test_methods_require_open_stream_raises(self):
        writer = self._make_one()
        methods = [
            writer.append(b"data"),
            writer.flush(),
            writer.simple_flush(),
            writer.close(),
            writer.finalize(),
            writer.state_lookup()
        ]
        for coro in methods:
            with self.assertRaisesRegex(ValueError, "Stream is not open"):
                await coro
