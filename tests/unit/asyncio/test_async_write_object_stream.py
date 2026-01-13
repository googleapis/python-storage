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

import unittest
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock
import pytest

from google.cloud.storage._experimental.asyncio.async_write_object_stream import (
    _AsyncWriteObjectStream,
)
from google.cloud import _storage_v2

BUCKET = "my-bucket"
OBJECT = "my-object"
GENERATION = 12345
WRITE_HANDLE = b"test-handle"
FULL_BUCKET_PATH = f"projects/_/buckets/{BUCKET}"


class TestAsyncWriteObjectStream(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        # Mocking transport internal structures
        mock_transport = MagicMock()
        mock_transport.bidi_write_object = mock.sentinel.bidi_write_object
        mock_transport._wrapped_methods = {
            mock.sentinel.bidi_write_object: mock.sentinel.wrapped_bidi_write_object
        }
        self.mock_client._client._transport = mock_transport

    # -------------------------------------------------------------------------
    # Initialization Tests
    # -------------------------------------------------------------------------

    def test_init_basic(self):
        stream = _AsyncWriteObjectStream(self.mock_client, BUCKET, OBJECT)
        self.assertEqual(stream.bucket_name, BUCKET)
        self.assertEqual(stream.object_name, OBJECT)
        self.assertEqual(stream._full_bucket_name, FULL_BUCKET_PATH)
        self.assertEqual(
            stream.metadata, (("x-goog-request-params", f"bucket={FULL_BUCKET_PATH}"),)
        )
        self.assertFalse(stream.is_stream_open)

    def test_init_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "client must be provided"):
            _AsyncWriteObjectStream(None, BUCKET, OBJECT)
        with self.assertRaisesRegex(ValueError, "bucket_name must be provided"):
            _AsyncWriteObjectStream(self.mock_client, None, OBJECT)
        with self.assertRaisesRegex(ValueError, "object_name must be provided"):
            _AsyncWriteObjectStream(self.mock_client, BUCKET, None)

    # -------------------------------------------------------------------------
    # Open Stream Tests
    # -------------------------------------------------------------------------

    @mock.patch(
        "google.cloud.storage._experimental.asyncio.async_write_object_stream.AsyncBidiRpc"
    )
    @pytest.mark.asyncio
    async def test_open_new_object(self, mock_rpc_cls):
        mock_rpc = mock_rpc_cls.return_value
        mock_rpc.open = AsyncMock()

        # We don't use spec here to avoid descriptor issues with nested protos
        mock_response = MagicMock()
        mock_response.persisted_size = 0
        mock_response.resource.generation = GENERATION
        mock_response.resource.size = 0
        mock_response.write_handle = WRITE_HANDLE
        mock_rpc.recv = AsyncMock(return_value=mock_response)

        stream = _AsyncWriteObjectStream(self.mock_client, BUCKET, OBJECT)
        await stream.open()

        # Check if BidiRpc was initialized with WriteObjectSpec
        call_args = mock_rpc_cls.call_args
        initial_request = call_args.kwargs["initial_request"]
        self.assertIsNotNone(initial_request.write_object_spec)
        self.assertEqual(initial_request.write_object_spec.resource.name, OBJECT)
        self.assertTrue(initial_request.write_object_spec.appendable)

        self.assertTrue(stream.is_stream_open)
        self.assertEqual(stream.write_handle, WRITE_HANDLE)
        self.assertEqual(stream.generation_number, GENERATION)

    @mock.patch(
        "google.cloud.storage._experimental.asyncio.async_write_object_stream.AsyncBidiRpc"
    )
    @pytest.mark.asyncio
    async def test_open_existing_object_with_token(self, mock_rpc_cls):
        mock_rpc = mock_rpc_cls.return_value
        mock_rpc.open = AsyncMock()

        # Ensure resource is None so persisted_size logic doesn't get overwritten by child mocks
        mock_response = MagicMock()
        mock_response.persisted_size = 1024
        mock_response.resource = None
        mock_response.write_handle = WRITE_HANDLE
        mock_rpc.recv = AsyncMock(return_value=mock_response)

        stream = _AsyncWriteObjectStream(
            self.mock_client,
            BUCKET,
            OBJECT,
            generation_number=GENERATION,
            routing_token="token-123",
        )
        await stream.open()

        # Verify AppendObjectSpec attributes
        initial_request = mock_rpc_cls.call_args.kwargs["initial_request"]
        self.assertIsNotNone(initial_request.append_object_spec)
        self.assertEqual(initial_request.append_object_spec.generation, GENERATION)
        self.assertEqual(initial_request.append_object_spec.routing_token, "token-123")
        self.assertEqual(stream.persisted_size, 1024)

    @mock.patch(
        "google.cloud.storage._experimental.asyncio.async_write_object_stream.AsyncBidiRpc"
    )
    @pytest.mark.asyncio
    async def test_open_metadata_merging(self, mock_rpc_cls):
        mock_rpc = mock_rpc_cls.return_value
        mock_rpc.open = AsyncMock()
        mock_rpc.recv = AsyncMock(return_value=MagicMock(resource=None))

        stream = _AsyncWriteObjectStream(self.mock_client, BUCKET, OBJECT)
        extra_metadata = [("x-custom", "val"), ("x-goog-request-params", "extra=param")]

        await stream.open(metadata=extra_metadata)

        # Verify that metadata combined bucket and extra params
        passed_metadata = mock_rpc_cls.call_args.kwargs["metadata"]
        meta_dict = dict(passed_metadata)
        self.assertEqual(meta_dict["x-custom"], "val")
        # Params should be comma separated
        params = meta_dict["x-goog-request-params"]
        self.assertIn(f"bucket={FULL_BUCKET_PATH}", params)
        self.assertIn("extra=param", params)

    @pytest.mark.asyncio
    async def test_open_already_open_raises(self):
        stream = _AsyncWriteObjectStream(self.mock_client, BUCKET, OBJECT)
        stream._is_stream_open = True
        with self.assertRaisesRegex(ValueError, "already open"):
            await stream.open()

    # -------------------------------------------------------------------------
    # Send & Recv & Close Tests
    # -------------------------------------------------------------------------

    @mock.patch(
        "google.cloud.storage._experimental.asyncio.async_write_object_stream.AsyncBidiRpc"
    )
    @pytest.mark.asyncio
    async def test_send_and_recv_logic(self, mock_rpc_cls):
        # Setup open stream
        mock_rpc = mock_rpc_cls.return_value
        mock_rpc.open = AsyncMock()
        mock_rpc.send = AsyncMock()  # Crucial: Must be AsyncMock
        mock_rpc.recv = AsyncMock(return_value=MagicMock(resource=None))

        stream = _AsyncWriteObjectStream(self.mock_client, BUCKET, OBJECT)
        await stream.open()

        # Test Send
        req = _storage_v2.BidiWriteObjectRequest(write_offset=0)
        await stream.send(req)
        mock_rpc.send.assert_awaited_with(req)

        # Test Recv with state update
        mock_response = MagicMock()
        mock_response.persisted_size = 5000
        mock_response.write_handle = b"new-handle"
        mock_response.resource = None
        mock_rpc.recv.return_value = mock_response

        res = await stream.recv()
        self.assertEqual(res.persisted_size, 5000)
        self.assertEqual(stream.persisted_size, 5000)
        self.assertEqual(stream.write_handle, b"new-handle")

    @pytest.mark.asyncio
    async def test_close_success(self):
        stream = _AsyncWriteObjectStream(self.mock_client, BUCKET, OBJECT)
        stream._is_stream_open = True
        stream.socket_like_rpc = AsyncMock()
        stream.socket_like_rpc.close = AsyncMock()

        await stream.close()
        stream.socket_like_rpc.close.assert_awaited_once()
        self.assertFalse(stream.is_stream_open)

    @pytest.mark.asyncio
    async def test_methods_require_open_raises(self):
        stream = _AsyncWriteObjectStream(self.mock_client, BUCKET, OBJECT)
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await stream.send(MagicMock())
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await stream.recv()
        with self.assertRaisesRegex(ValueError, "Stream is not open"):
            await stream.close()
