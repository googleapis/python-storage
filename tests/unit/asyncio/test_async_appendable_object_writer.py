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

BUCKET = "test-bucket"
OBJECT = "test-object"
GENERATION = 123
WRITE_HANDLE = b"test-write-handle"
PERSISTED_SIZE = 456
EIGHT_MIB = 8 * 1024 * 1024


class TestIsWriteRetryable(unittest.TestCase):
    def test_transient_errors(self):
        for exc_type in [
            exceptions.InternalServerError,
            exceptions.ServiceUnavailable,
            exceptions.DeadlineExceeded,
            exceptions.TooManyRequests,
        ]:
            self.assertTrue(_is_write_retryable(exc_type("error")))

    def test_aborted_with_redirect_proto(self):
        # Direct redirect error wrapped in Aborted
        redirect = BidiWriteObjectRedirectedError(routing_token="token")
        exc = exceptions.Aborted("aborted", errors=[redirect])
        self.assertTrue(_is_write_retryable(exc))

    def test_aborted_with_trailers(self):
        # Redirect hidden in trailers
        status = status_pb2.Status()
        detail = status.details.add()
        detail.type_url = "type.googleapis.com/google.storage.v2.BidiWriteObjectRedirectedError"

        # Correctly serialize the proto message to bytes for the detail value
        redirect_proto = BidiWriteObjectRedirectedError(routing_token="rt2")
        detail.value = BidiWriteObjectRedirectedError.serialize(redirect_proto)

        exc = exceptions.Aborted("aborted")
        exc.trailing_metadata = [("grpc-status-details-bin", status.SerializeToString())]
        self.assertTrue(_is_write_retryable(exc))

    def test_non_retryable(self):
        self.assertFalse(_is_write_retryable(exceptions.BadRequest("bad")))
        self.assertFalse(_is_write_retryable(exceptions.Aborted("just aborted")))


class TestAsyncAppendableObjectWriter(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_client = mock.AsyncMock()
        # Patch the stream class used internally
        self.mock_stream_cls = mock.patch(
            "google.cloud.storage._experimental.asyncio.async_appendable_object_writer._AsyncWriteObjectStream"
        ).start()
        self.mock_stream = self.mock_stream_cls.return_value

        # Default mock stream state
        self.mock_stream.is_stream_open = False
        self.mock_stream.persisted_size = 0
        self.mock_stream.generation_number = GENERATION
        self.mock_stream.write_handle = WRITE_HANDLE

    def tearDown(self):
        mock.patch.stopall()

    def _make_one(self, **kwargs):
        return AsyncAppendableObjectWriter(
            self.mock_client, BUCKET, OBJECT, **kwargs
        )

    # -------------------------------------------------------------------------
    # Initialization Tests
    # -------------------------------------------------------------------------

    def test_init_defaults(self):
        writer = self._make_one()
        self.assertEqual(writer.client, self.mock_client)
        self.assertEqual(writer.bucket_name, BUCKET)
        self.assertEqual(writer.object_name, OBJECT)
        self.assertIsNone(writer.generation)
        self.assertIsNone(writer.write_handle)
        self.assertFalse(writer._is_stream_open)
        self.assertIsNone(writer.persisted_size)
        self.assertEqual(writer.bytes_appended_since_last_flush, 0)

    def test_init_with_optional_args(self):
        writer = self._make_one(
            generation=GENERATION,
            write_handle=WRITE_HANDLE,
        )
        self.assertEqual(writer.generation, GENERATION)
        self.assertEqual(writer.write_handle, WRITE_HANDLE)

    def test_init_with_writer_options(self):
        writer = self._make_one(writer_options={"FLUSH_INTERVAL_BYTES": EIGHT_MIB})
        self.assertEqual(writer.flush_interval, EIGHT_MIB)

    def test_init_validation_chunk_size(self):
        with self.assertRaises(exceptions.OutOfRange):
            self._make_one(writer_options={"FLUSH_INTERVAL_BYTES": _MAX_CHUNK_SIZE_BYTES - 1})

    def test_init_validation_chunk_multiple(self):
        with self.assertRaises(exceptions.OutOfRange):
            self._make_one(writer_options={"FLUSH_INTERVAL_BYTES": _MAX_CHUNK_SIZE_BYTES + 1})

    def test_init_raises_if_crc32c_c_extension_is_missing(self):
        with mock.patch("google.cloud.storage._experimental.asyncio._utils.google_crc32c") as mock_crc:
            mock_crc.implementation = "python"
            with self.assertRaisesRegex(exceptions.FailedPrecondition, "google-crc32c package is not installed"):
                self._make_one()

    # -------------------------------------------------------------------------
    # Helper Method Tests
    # -------------------------------------------------------------------------

    async def test_state_lookup(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream

        self.mock_stream.recv.return_value = storage_type.BidiWriteObjectResponse(
            persisted_size=PERSISTED_SIZE
        )

        resp = await writer.state_lookup()

        self.mock_stream.send.assert_awaited_once_with(
            storage_type.BidiWriteObjectRequest(state_lookup=True)
        )
        self.assertEqual(resp, PERSISTED_SIZE)
        self.assertEqual(writer.persisted_size, PERSISTED_SIZE)

    async def test_state_lookup_not_open_raises(self):
        writer = self._make_one()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await writer.state_lookup()

    async def test_unimplemented_methods(self):
        writer = self._make_one()
        with self.assertRaises(NotImplementedError):
            await writer.append_from_string("data")
        with self.assertRaises(NotImplementedError):
            await writer.append_from_stream(mock.Mock())

    # -------------------------------------------------------------------------
    # Open & Error Handling Tests
    # -------------------------------------------------------------------------

    async def test_open_success(self):
        writer = self._make_one()
        self.mock_stream.generation_number = GENERATION
        self.mock_stream.write_handle = WRITE_HANDLE
        self.mock_stream.persisted_size = 0

        await writer.open()

        self.assertTrue(writer._is_stream_open)
        self.assertEqual(writer.generation, GENERATION)
        self.assertEqual(writer.write_handle, WRITE_HANDLE)
        self.assertEqual(writer.persisted_size, 0)

        self.mock_stream_cls.assert_called_with(
            client=self.mock_client,
            bucket_name=BUCKET,
            object_name=OBJECT,
            generation_number=None,
            write_handle=None,
            routing_token=None,
        )
        self.mock_stream.open.assert_awaited_once()

    async def test_open_appendable_object_writer_existing_object(self):
        # Verify opening with existing generation uses AppendObjectSpec implicitly via stream init
        writer = self._make_one(generation=GENERATION, write_handle=WRITE_HANDLE)
        self.mock_stream.generation_number = GENERATION
        self.mock_stream.write_handle = WRITE_HANDLE
        self.mock_stream.persisted_size = PERSISTED_SIZE

        await writer.open()

        # Check constructor was called with generation/handle
        self.mock_stream_cls.assert_called_with(
            client=self.mock_client,
            bucket_name=BUCKET,
            object_name=OBJECT,
            generation_number=GENERATION,
            write_handle=WRITE_HANDLE,
            routing_token=None,
        )
        self.assertEqual(writer.persisted_size, PERSISTED_SIZE)

    async def test_open_with_routing_token_and_metadata(self):
        writer = self._make_one()
        writer._routing_token = "prev-token"
        metadata = [("key", "val")]

        await writer.open(metadata=metadata)

        self.mock_stream_cls.assert_called_with(
            client=self.mock_client,
            bucket_name=BUCKET,
            object_name=OBJECT,
            generation_number=None,
            write_handle=None,
            routing_token="prev-token",
        )
        call_kwargs = self.mock_stream.open.call_args[1]
        passed_metadata = call_kwargs['metadata']
        self.assertIn(("x-goog-request-params", "routing_token=prev-token"), passed_metadata)
        self.assertIsNone(writer._routing_token)

    async def test_open_when_already_open_raises(self):
        writer = self._make_one()
        writer._is_stream_open = True
        with self.assertRaisesRegex(ValueError, "Underlying bidi-gRPC stream is already open"):
            await writer.open()

    def test_on_open_error_extraction(self):
        writer = self._make_one()

        # 1. Direct Redirect Error
        redirect = BidiWriteObjectRedirectedError(
            routing_token="rt",
            write_handle=storage_type.BidiWriteHandle(handle=b"wh"),
            generation=999
        )
        writer._on_open_error(exceptions.Aborted("e", errors=[redirect]))

        self.assertEqual(writer._routing_token, "rt")
        self.assertEqual(writer.write_handle.handle, b"wh")
        self.assertEqual(writer.generation, 999)

        # 2. Trailer Error
        status = status_pb2.Status()
        detail = status.details.add()
        detail.type_url = "type.googleapis.com/google.storage.v2.BidiWriteObjectRedirectedError"
        detail.value = BidiWriteObjectRedirectedError.serialize(
            BidiWriteObjectRedirectedError(routing_token="rt2")
        )

        exc = exceptions.Aborted("e")
        exc.trailing_metadata = [("grpc-status-details-bin", status.SerializeToString())]

        writer._on_open_error(exc)
        self.assertEqual(writer._routing_token, "rt2")

    # -------------------------------------------------------------------------
    # Append Tests
    # -------------------------------------------------------------------------

    async def test_append_not_open_raises(self):
        writer = self._make_one()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await writer.append(b"data")

    async def test_append_empty_data_does_nothing(self):
        writer = self._make_one()
        writer._is_stream_open = True
        with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
            await writer.append(b"")
            MockManager.assert_not_called()

    async def test_append_propagates_non_retryable_errors(self):
        """Verify non-retryable errors bubble up."""
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream

        with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
            # Simulate RetryManager raising a hard error
            MockManager.return_value.execute.side_effect = exceptions.BadRequest("bad")

            with self.assertRaises(exceptions.BadRequest):
                await writer.append(b"data")

    async def test_append_basic_flow_integration(self):
        """Verify append sets up RetryManager and orchestrates chunks."""
        writer = self._make_one(write_handle=b"h1", generation=1)
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.persisted_size = 0

        data = b"a" * (_MAX_CHUNK_SIZE_BYTES + 10) # 2MB + 10 bytes

        with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
            mock_manager_instance = MockManager.return_value

            async def mock_execute(state, policy):
                generator_factory = MockManager.call_args[0][1]
                # Strategy generates chunks (we use dummy ones for integration check)
                dummy_requests = [
                    storage_type.BidiWriteObjectRequest(write_offset=0),
                    storage_type.BidiWriteObjectRequest(write_offset=_MAX_CHUNK_SIZE_BYTES)
                ]
                gen = generator_factory(dummy_requests, state)

                self.mock_stream.recv.side_effect = [
                    storage_type.BidiWriteObjectResponse(persisted_size=100, write_handle=b"h2"),
                    None
                ]
                async for _ in gen: pass

            mock_manager_instance.execute.side_effect = mock_execute

            await writer.append(data)

            self.assertEqual(writer.persisted_size, 100)
            self.assertEqual(writer.write_handle, b"h2")
            self.assertEqual(self.mock_stream.send.await_count, 2)
            # Last chunk should have state_lookup=True
            self.assertTrue(self.mock_stream.send.await_args_list[-1][0][0].state_lookup)

    async def test_append_flushes_when_interval_reached(self):
        """Verify generator respects flush flag from strategy."""
        # Flush interval matches 2 chunks
        flush_interval = _MAX_CHUNK_SIZE_BYTES * 2
        writer = self._make_one(writer_options={"FLUSH_INTERVAL_BYTES": flush_interval})
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream

        data = b"a" * flush_interval

        with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
            mock_manager_instance = MockManager.return_value

            async def mock_execute(state, policy):
                generator_factory = MockManager.call_args[0][1]

                # Simulate strategy identifying a flush point
                req_with_flush = storage_type.BidiWriteObjectRequest(flush=True)
                gen = generator_factory([req_with_flush], state)

                self.mock_stream.recv.return_value = None
                async for _ in gen: pass

            mock_manager_instance.execute.side_effect = mock_execute
            await writer.append(data)

            # Verify sent request had flush=True
            sent_request = self.mock_stream.send.call_args[0][0]
            self.assertTrue(sent_request.flush)

    async def test_append_sequential_calls_update_state(self):
        """Test state carry-over between two append calls."""
        writer = self._make_one(write_handle=b"h1", generation=1)
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.persisted_size = 0

        with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
            # 1. First Append
            async def execute_1(state, policy):
                # Simulate server acknowledging 100 bytes
                state["write_state"].persisted_size = 100
                writer.write_obj_stream.persisted_size = 100

            MockManager.return_value.execute.side_effect = execute_1
            await writer.append(b"a" * 100)

            self.assertEqual(writer.persisted_size, 100)

            # 2. Second Append
            async def execute_2(state, policy):
                # Verify state passed to manager starts where we left off
                assert state["write_state"].persisted_size == 100
                state["write_state"].persisted_size = 200

            MockManager.return_value.execute.side_effect = execute_2
            await writer.append(b"b" * 100)

            self.assertEqual(writer.persisted_size, 200)

    async def test_append_recovery_flow(self):
        """Test internal generator logic when a retry occurs (Attempt > 1)."""
        writer = self._make_one(write_handle=b"h1", generation=1)
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.persisted_size = 0

        async def mock_aaow_open(metadata=None):
            writer._is_stream_open = True
            writer.write_obj_stream = self.mock_stream
            writer.persisted_size = 4 # Server says 4 bytes persisted
            writer.write_handle = b"h_new"

        with mock.patch.object(writer, "open", side_effect=mock_aaow_open) as mock_writer_open:
            with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:

                async def mock_execute(state, policy):
                    factory = MockManager.call_args[0][1]

                    # --- SIMULATE ATTEMPT 1 (Fail) ---
                    gen1 = factory([], state)
                    try: await gen1.__anext__()
                    except: pass

                    # --- SIMULATE ATTEMPT 2 (Recovery) ---
                    # Logic should: close old stream, open new, rewind buffer, generate new requests
                    gen2 = factory([], state)
                    self.mock_stream.is_stream_open = True
                    self.mock_stream.recv.side_effect = [None]
                    async for _ in gen2: pass

                MockManager.return_value.execute.side_effect = mock_execute

                await writer.append(b"1234567890")

                # Recovery Assertions
                self.mock_stream.close.assert_awaited()
                mock_writer_open.assert_awaited()
                self.assertEqual(writer.write_handle, b"h_new")
                self.assertEqual(writer.persisted_size, 4)

    async def test_append_metadata_injection(self):
        """Verify providing metadata forces a restart (Attempt 1 logic)."""
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        custom_meta = [("x-test", "true")]

        with mock.patch.object(writer, "open", new_callable=mock.AsyncMock) as mock_writer_open:
            with mock.patch("google.cloud.storage._experimental.asyncio.async_appendable_object_writer._BidiStreamRetryManager") as MockManager:
                async def mock_execute(state, policy):
                    factory = MockManager.call_args[0][1]
                    gen = factory([], state)
                    self.mock_stream.recv.return_value = None
                    async for _ in gen: pass

                MockManager.return_value.execute.side_effect = mock_execute
                await writer.append(b"data", metadata=custom_meta)

                self.mock_stream.close.assert_awaited()
                mock_writer_open.assert_awaited_with(metadata=custom_meta)

    # -------------------------------------------------------------------------
    # Flush, Close, Finalize Tests
    # -------------------------------------------------------------------------

    async def test_flush(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.bytes_appended_since_last_flush = 50

        self.mock_stream.recv.return_value = storage_type.BidiWriteObjectResponse(
            persisted_size=100
        )

        res = await writer.flush()

        self.mock_stream.send.assert_awaited_with(
            storage_type.BidiWriteObjectRequest(flush=True, state_lookup=True)
        )
        self.assertEqual(res, 100)
        self.assertEqual(writer.bytes_appended_since_last_flush, 0)

    async def test_flush_not_open_raises(self):
        writer = self._make_one()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await writer.flush()

    async def test_simple_flush(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream

        await writer.simple_flush()

        self.mock_stream.send.assert_awaited_with(
            storage_type.BidiWriteObjectRequest(flush=True)
        )

    async def test_simple_flush_not_open_raises(self):
        writer = self._make_one()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await writer.simple_flush()

    async def test_close(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        writer.persisted_size = 50

        res = await writer.close()

        self.mock_stream.close.assert_awaited()
        self.assertFalse(writer._is_stream_open)
        self.assertEqual(res, 50)

    async def test_close_not_open_raises(self):
        writer = self._make_one()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await writer.close()

    async def test_finalize(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.write_obj_stream = self.mock_stream
        resource = storage_type.Object(size=999)
        self.mock_stream.recv.return_value = storage_type.BidiWriteObjectResponse(
            resource=resource
        )

        res = await writer.finalize()

        self.mock_stream.send.assert_awaited_with(
            storage_type.BidiWriteObjectRequest(finish_write=True)
        )
        self.assertEqual(writer.object_resource, resource)
        self.assertEqual(writer.persisted_size, 999)
        self.assertEqual(res, resource)

    async def test_finalize_not_open_raises(self):
        writer = self._make_one()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await writer.finalize()

    # -------------------------------------------------------------------------
    # Append From File Tests
    # -------------------------------------------------------------------------

    async def test_append_from_file(self):
        writer = self._make_one()
        writer._is_stream_open = True
        writer.append = mock.AsyncMock()

        fp = io.BytesIO(b"1234567890")
        await writer.append_from_file(fp, block_size=4)

        self.assertEqual(writer.append.await_count, 3)
