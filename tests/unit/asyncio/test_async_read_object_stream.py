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

import pytest
from unittest import mock

from google.cloud.storage._experimental.asyncio.async_abstract_object_stream import (
    _AsyncAbstractObjectStream,
)
from google.cloud.storage._experimental.asyncio.async_read_object_stream import (
    _AsyncReadObjectStream,
)


@pytest.fixture
def mock_client():
    """A mock client for testing."""
    mock_rpc = mock.Mock(name="rpc")
    mock_transport = mock.Mock(name="transport")
    mock_transport.bidi_read_object = "bidi_read_object_key"
    mock_transport._wrapped_methods = {"bidi_read_object_key": mock_rpc}
    mock_gapic_client = mock.Mock(name="gapic_client")
    mock_gapic_client._transport = mock_transport
    mock_client = mock.Mock(name="client")
    mock_client._client = mock_gapic_client
    return mock_client


def test_inheritance():
    """Test that _AsyncReadObjectStream inherits from _AsyncAbstractObjectStream."""
    assert issubclass(_AsyncReadObjectStream, _AsyncAbstractObjectStream)


@mock.patch(
    "google.cloud.storage._experimental.asyncio.async_read_object_stream.AsyncBidiRpc"
)
@mock.patch(
    "google.cloud.storage._experimental.asyncio.async_read_object_stream._storage_v2"
)
def test_init(mock_storage_v2, mock_async_bidi_rpc, mock_client):
    """Test the constructor of _AsyncReadObjectStream."""
    mock_rpc = mock_client._client._transport._wrapped_methods["bidi_read_object_key"]
    bucket_name = "test-bucket"
    object_name = "test-object"
    generation = 12345
    read_handle = b"some-handle"

    # Test with all parameters
    stream = _AsyncReadObjectStream(
        mock_client,
        bucket_name=bucket_name,
        object_name=object_name,
        generation_number=generation,
        read_handle=read_handle,
    )

    assert stream.client is mock_client
    assert stream.bucket_name == bucket_name
    assert stream.object_name == object_name
    assert stream.generation_number == generation
    assert stream.read_handle == read_handle

    full_bucket_name = f"projects/_/buckets/{bucket_name}"
    assert stream._full_bucket_name == full_bucket_name
    assert stream.rpc is mock_rpc

    mock_storage_v2.BidiReadObjectSpec.assert_called_once_with(
        bucket=full_bucket_name, object=object_name
    )
    mock_read_object_spec = mock_storage_v2.BidiReadObjectSpec.return_value
    mock_storage_v2.BidiReadObjectRequest.assert_called_once_with(
        read_object_spec=mock_read_object_spec
    )
    mock_initial_request = mock_storage_v2.BidiReadObjectRequest.return_value

    expected_metadata = (("x-goog-request-params", f"bucket={full_bucket_name}"),)
    assert stream.metadata == expected_metadata

    mock_async_bidi_rpc.assert_called_once_with(
        mock_rpc, initial_request=mock_initial_request, metadata=expected_metadata
    )
    assert stream.socket_like_rpc is mock_async_bidi_rpc.return_value

    # Reset mocks for the next test case
    mock_storage_v2.reset_mock()
    mock_async_bidi_rpc.reset_mock()

    # Test with default parameters
    stream_defaults = _AsyncReadObjectStream(mock_client)
    assert stream_defaults.client is mock_client
    assert stream_defaults.bucket_name is None
    assert stream_defaults.object_name is None
    assert stream_defaults.generation_number is None
    assert stream_defaults.read_handle is None

    # The following asserts the behavior with None values.
    full_bucket_name_none = "projects/_/buckets/None"
    assert stream_defaults._full_bucket_name == full_bucket_name_none

    mock_storage_v2.BidiReadObjectSpec.assert_called_once_with(
        bucket=full_bucket_name_none, object=None
    )
    mock_read_object_spec_none = mock_storage_v2.BidiReadObjectSpec.return_value
    mock_storage_v2.BidiReadObjectRequest.assert_called_once_with(
        read_object_spec=mock_read_object_spec_none
    )
    mock_initial_request_none = mock_storage_v2.BidiReadObjectRequest.return_value

    expected_metadata_none = (
        ("x-goog-request-params", f"bucket={full_bucket_name_none}"),
    )
    assert stream_defaults.metadata == expected_metadata_none

    mock_async_bidi_rpc.assert_called_once_with(
        mock_rpc,
        initial_request=mock_initial_request_none,
        metadata=expected_metadata_none,
    )


@pytest.mark.asyncio
async def test_open(mock_client):
    """Test open() when generation_number is initially None."""
    stream = _AsyncReadObjectStream(mock_client, bucket_name="b", object_name="o")
    stream.socket_like_rpc = mock.AsyncMock()
    stream.generation_number = None  # Explicitly set for clarity

    mock_response = mock.Mock()
    mock_response.metadata.generation = 98765
    mock_response.read_handle = b"test-read-handle"
    stream.socket_like_rpc.recv.return_value = mock_response

    await stream.open()

    stream.socket_like_rpc.open.assert_awaited_once()
    stream.socket_like_rpc.recv.assert_awaited_once()
    assert stream.generation_number == 98765
    assert stream.read_handle == b"test-read-handle"


@pytest.mark.asyncio
async def test_open_with_generation_set(mock_client):
    """Test open() when generation_number is already set."""
    initial_generation = 12345
    stream = _AsyncReadObjectStream(
        mock_client,
        bucket_name="b",
        object_name="o",
        generation_number=initial_generation,
    )
    stream.socket_like_rpc = mock.AsyncMock()

    mock_response = mock.Mock()
    mock_response.metadata.generation = 98765
    mock_response.read_handle = b"test-read-handle"
    stream.socket_like_rpc.recv.return_value = mock_response

    await stream.open()

    stream.socket_like_rpc.open.assert_awaited_once()
    stream.socket_like_rpc.recv.assert_awaited_once()
    assert stream.generation_number == initial_generation  # Should not change
    assert stream.read_handle == b"test-read-handle"


@pytest.mark.asyncio
async def test_close(mock_client):
    """Test close()."""
    stream = _AsyncReadObjectStream(mock_client)
    stream.socket_like_rpc = mock.AsyncMock()
    await stream.close()
    stream.socket_like_rpc.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_send(mock_client):
    """Test send()."""
    stream = _AsyncReadObjectStream(mock_client)
    stream.socket_like_rpc = mock.AsyncMock()
    mock_request = mock.Mock()
    await stream.send(mock_request)
    stream.socket_like_rpc.send.assert_awaited_once_with(mock_request)


@pytest.mark.asyncio
async def test_recv(mock_client):
    """Test recv()."""
    stream = _AsyncReadObjectStream(mock_client)
    stream.socket_like_rpc = mock.AsyncMock()
    mock_response = mock.Mock()
    stream.socket_like_rpc.recv.return_value = mock_response
    response = await stream.recv()
    stream.socket_like_rpc.recv.assert_awaited_once()
    assert response is mock_response
