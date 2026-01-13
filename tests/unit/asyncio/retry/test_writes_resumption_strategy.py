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
from datetime import datetime

import pytest
import google_crc32c
from google.rpc import status_pb2
from google.api_core import exceptions

from google.cloud._storage_v2.types import storage as storage_type
from google.cloud.storage._experimental.asyncio.retry.writes_resumption_strategy import (
    _WriteState,
    _WriteResumptionStrategy,
)
from google.cloud._storage_v2.types.storage import BidiWriteObjectRedirectedError


class TestWriteResumptionStrategy(unittest.TestCase):
    def _make_one(self):
        return _WriteResumptionStrategy()

    # -------------------------------------------------------------------------
    # Tests for generate_requests
    # -------------------------------------------------------------------------

    def test_generate_requests_initial_chunking(self):
        """Verify initial data generation starts at offset 0 and chunks correctly."""
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"abcdefghij")
        write_state = _WriteState(chunk_size=3, user_buffer=mock_buffer)
        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)

        # Expected: 4 requests (3, 3, 3, 1)
        self.assertEqual(len(requests), 4)

        # Verify Request 1
        self.assertEqual(requests[0].write_offset, 0)
        self.assertEqual(requests[0].checksummed_data.content, b"abc")

        # Verify Request 2
        self.assertEqual(requests[1].write_offset, 3)
        self.assertEqual(requests[1].checksummed_data.content, b"def")

        # Verify Request 3
        self.assertEqual(requests[2].write_offset, 6)
        self.assertEqual(requests[2].checksummed_data.content, b"ghi")

        # Verify Request 4
        self.assertEqual(requests[3].write_offset, 9)
        self.assertEqual(requests[3].checksummed_data.content, b"j")

    def test_generate_requests_resumption(self):
        """
        Verify request generation when resuming.
        The strategy should generate chunks starting from the current 'bytes_sent'.
        """
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"0123456789")
        write_state = _WriteState(chunk_size=4, user_buffer=mock_buffer)

        # Simulate resumption state: 4 bytes already sent/persisted
        write_state.persisted_size = 4
        write_state.bytes_sent = 4
        # Buffer must be seeked to 4 before calling generate
        mock_buffer.seek(4)

        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)

        # Since 4 bytes are done, we expect remaining 6 bytes: [4 bytes, 2 bytes]
        self.assertEqual(len(requests), 2)

        # Check first generated request starts at offset 4
        self.assertEqual(requests[0].write_offset, 4)
        self.assertEqual(requests[0].checksummed_data.content, b"4567")

        # Check second generated request starts at offset 8
        self.assertEqual(requests[1].write_offset, 8)
        self.assertEqual(requests[1].checksummed_data.content, b"89")

    def test_generate_requests_empty_file(self):
        """Verify request sequence for an empty file."""
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"")
        write_state = _WriteState(chunk_size=4, user_buffer=mock_buffer)
        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)

        self.assertEqual(len(requests), 0)

    def test_generate_requests_checksum_verification(self):
        """Verify CRC32C is calculated correctly for each chunk."""
        strategy = self._make_one()
        chunk_data = b"test_data"
        mock_buffer = io.BytesIO(chunk_data)
        write_state = _WriteState(chunk_size=10, user_buffer=mock_buffer)
        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)

        expected_crc = google_crc32c.Checksum(chunk_data).digest()
        expected_int = int.from_bytes(expected_crc, "big")
        self.assertEqual(requests[0].checksummed_data.crc32c, expected_int)

    def test_generate_requests_flush_logic_exact_interval(self):
        """Verify the flush bit is set exactly when the interval is reached."""
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"A" * 12)
        # 2 byte chunks, flush every 4 bytes
        write_state = _WriteState(
            chunk_size=2, user_buffer=mock_buffer, flush_interval=4
        )
        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)

        # Request index 1 (4 bytes total) should have flush=True
        self.assertFalse(requests[0].flush)
        self.assertTrue(requests[1].flush)

        # Request index 3 (8 bytes total) should have flush=True
        self.assertFalse(requests[2].flush)
        self.assertTrue(requests[3].flush)

        # Verify counter reset in state
        self.assertEqual(write_state.bytes_since_last_flush, 0)

    def test_generate_requests_flush_logic_none_interval(self):
        """Verify flush is never set if interval is None."""
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"A" * 10)
        write_state = _WriteState(
            chunk_size=2, user_buffer=mock_buffer, flush_interval=None
        )
        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)

        for req in requests:
            self.assertFalse(req.flush)

    def test_generate_requests_flush_logic_data_less_than_interval(self):
        """Verify flush is not set if data sent is less than interval."""
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"A" * 5)
        # Flush every 10 bytes
        write_state = _WriteState(
            chunk_size=2, user_buffer=mock_buffer, flush_interval=10
        )
        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)

        # Total 5 bytes < 10 bytes interval
        for req in requests:
            self.assertFalse(req.flush)

        self.assertEqual(write_state.bytes_since_last_flush, 5)

    def test_generate_requests_honors_finalized_state(self):
        """If state is already finalized, no requests should be generated."""
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"data")
        write_state = _WriteState(chunk_size=4, user_buffer=mock_buffer)
        write_state.is_finalized = True
        state = {"write_state": write_state}

        requests = strategy.generate_requests(state)
        self.assertEqual(len(requests), 0)

    @pytest.mark.asyncio
    async def test_generate_requests_after_failure_and_recovery(self):
        """
        Verify recovery and resumption flow (Integration of recover + generate).
        """
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"0123456789abcdef")  # 16 bytes
        mock_spec = storage_type.AppendObjectSpec(object_="test-object")
        write_state = _WriteState(mock_spec, chunk_size=4, user_buffer=mock_buffer)
        state = {"write_state": write_state}

        # Simulate initial progress: sent 8 bytes
        write_state.bytes_sent = 8
        mock_buffer.seek(8)

        strategy.update_state_from_response(
            storage_type.BidiWriteObjectResponse(
                persisted_size=4,
                write_handle=storage_type.BidiWriteHandle(handle=b"handle-1"),
            ),
            state,
        )

        # Simulate Failure Triggering Recovery
        await strategy.recover_state_on_failure(Exception("network error"), state)

        # Assertions after recovery
        # 1. Buffer should rewind to persisted_size (4)
        self.assertEqual(mock_buffer.tell(), 4)
        # 2. bytes_sent should track persisted_size (4)
        self.assertEqual(write_state.bytes_sent, 4)

        requests = strategy.generate_requests(state)

        # Remaining data from offset 4 to 16 (12 bytes total)
        # Chunks: [4-8], [8-12], [12-16]
        self.assertEqual(len(requests), 3)

        # Verify resumption offset
        self.assertEqual(requests[0].write_offset, 4)
        self.assertEqual(requests[0].checksummed_data.content, b"4567")

    # -------------------------------------------------------------------------
    # Tests for update_state_from_response
    # -------------------------------------------------------------------------

    def test_update_state_from_response_all_fields(self):
        """Verify all fields from a BidiWriteObjectResponse update the state."""
        strategy = self._make_one()
        write_state = _WriteState(chunk_size=4, user_buffer=io.BytesIO())
        state = {"write_state": write_state}

        # 1. Update persisted_size
        strategy.update_state_from_response(
            storage_type.BidiWriteObjectResponse(persisted_size=123), state
        )
        self.assertEqual(write_state.persisted_size, 123)

        # 2. Update write_handle
        handle = storage_type.BidiWriteHandle(handle=b"new-handle")
        strategy.update_state_from_response(
            storage_type.BidiWriteObjectResponse(write_handle=handle), state
        )
        self.assertEqual(write_state.write_handle, handle)

        # 3. Update from Resource (finalization)
        resource = storage_type.Object(size=1000, finalize_time=datetime.now())
        strategy.update_state_from_response(
            storage_type.BidiWriteObjectResponse(resource=resource), state
        )
        self.assertEqual(write_state.persisted_size, 1000)
        self.assertTrue(write_state.is_finalized)

    def test_update_state_from_response_none(self):
        """Verify None response doesn't crash."""
        strategy = self._make_one()
        write_state = _WriteState(chunk_size=4, user_buffer=io.BytesIO())
        state = {"write_state": write_state}
        strategy.update_state_from_response(None, state)
        self.assertEqual(write_state.persisted_size, 0)

    # -------------------------------------------------------------------------
    # Tests for recover_state_on_failure
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_recover_state_on_failure_rewind_logic(self):
        """Verify buffer seek and counter resets on generic failure (Non-redirect)."""
        strategy = self._make_one()
        mock_buffer = io.BytesIO(b"0123456789")
        write_state = _WriteState(chunk_size=2, user_buffer=mock_buffer)

        # Simulate progress: sent 8 bytes, but server only persisted 4
        write_state.bytes_sent = 8
        write_state.persisted_size = 4
        write_state.bytes_since_last_flush = 2
        mock_buffer.seek(8)

        # Simulate generic 503 error without trailers
        await strategy.recover_state_on_failure(
            exceptions.ServiceUnavailable("busy"), {"write_state": write_state}
        )

        # Buffer must be seeked back to 4
        self.assertEqual(mock_buffer.tell(), 4)
        self.assertEqual(write_state.bytes_sent, 4)
        # Flush counter must be reset to avoid incorrect firing after resume
        self.assertEqual(write_state.bytes_since_last_flush, 0)

    @pytest.mark.asyncio
    async def test_recover_state_on_failure_direct_redirect(self):
        """Verify handling when the error is a BidiWriteObjectRedirectedError."""
        strategy = self._make_one()
        write_state = _WriteState(chunk_size=4, user_buffer=io.BytesIO())
        state = {"write_state": write_state}

        redirect = BidiWriteObjectRedirectedError(
            routing_token="tok-1", write_handle=b"h-1"
        )

        await strategy.recover_state_on_failure(redirect, state)

        self.assertEqual(write_state.routing_token, "tok-1")
        self.assertEqual(write_state.write_handle, b"h-1")

    @pytest.mark.asyncio
    async def test_recover_state_on_failure_wrapped_redirect(self):
        """Verify handling when RedirectedError is inside Aborted.errors."""
        strategy = self._make_one()
        write_state = _WriteState(chunk_size=4, user_buffer=io.BytesIO())

        redirect = BidiWriteObjectRedirectedError(routing_token="tok-wrapped")
        # google-api-core Aborted often wraps multiple errors
        error = exceptions.Aborted("conflict", errors=[redirect])

        await strategy.recover_state_on_failure(error, {"write_state": write_state})

        self.assertEqual(write_state.routing_token, "tok-wrapped")

    @pytest.mark.asyncio
    async def test_recover_state_on_failure_trailer_metadata_redirect(self):
        """Verify complex parsing from 'grpc-status-details-bin' in trailers."""
        strategy = self._make_one()
        write_state = _WriteState(chunk_size=4, user_buffer=io.BytesIO())

        # 1. Setup Redirect Proto
        redirect_proto = BidiWriteObjectRedirectedError(routing_token="metadata-token")

        # 2. Setup Status Proto Detail
        status = status_pb2.Status()
        detail = status.details.add()
        detail.type_url = (
            "type.googleapis.com/google.storage.v2.BidiWriteObjectRedirectedError"
        )
        # In a real environment, detail.value is the serialized proto
        detail.value = BidiWriteObjectRedirectedError.to_json(redirect_proto).encode()

        # 3. Create Mock Error with Trailers
        mock_error = mock.MagicMock(spec=exceptions.Aborted)
        mock_error.errors = []  # No direct errors
        mock_error.trailing_metadata.return_value = [
            ("grpc-status-details-bin", status.SerializeToString())
        ]

        # 4. Patch deserialize to handle the binary value
        with mock.patch(
            "google.cloud._storage_v2.types.storage.BidiWriteObjectRedirectedError.deserialize",
            return_value=redirect_proto,
        ):
            await strategy.recover_state_on_failure(
                mock_error, {"write_state": write_state}
            )

        self.assertEqual(write_state.routing_token, "metadata-token")

    def test_write_state_initialization(self):
        """Verify WriteState starts with clean counters."""
        buffer = io.BytesIO(b"test")
        ws = _WriteState(chunk_size=10, user_buffer=buffer, flush_interval=100)

        self.assertEqual(ws.persisted_size, 0)
        self.assertEqual(ws.bytes_sent, 0)
        self.assertEqual(ws.bytes_since_last_flush, 0)
        self.assertEqual(ws.flush_interval, 100)
        self.assertFalse(ws.is_finalized)
