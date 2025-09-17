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


def test_inheritance():
    """Test that _AsyncReadObjectStream inherits from _AsyncAbstractObjectStream."""
    assert issubclass(_AsyncReadObjectStream, _AsyncAbstractObjectStream)


@mock.patch(
    "google.cloud.storage._experimental.asyncio.async_read_object_stream.AsyncBidiRpc"
)
@mock.patch(
    "google.cloud.storage._experimental.asyncio.async_read_object_stream._storage_v2"
)
def test_init(mock_storage_v2, mock_async_bidi_rpc):
    """Test the constructor of _AsyncReadObjectStream."""
    # Setup mock client
    mock_rpc = mock.Mock(name="rpc")
    mock_transport = mock.Mock(name="transport")
    mock_transport.bidi_read_object = "bidi_read_object_key"
    mock_transport._wrapped_methods = {"bidi_read_object_key": mock_rpc}
    mock_gapic_client = mock.Mock(name="gapic_client")
    mock_gapic_client._transport = mock_transport
    mock_client = mock.Mock(name="client")
    mock_client._client = mock_gapic_client

    bucket_name = "test-bucket"
    object_name = "test-object"
    generation = 12345
    read_handle = "some-handle"

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
async def test_async_methods_are_awaitable():
    """Test that the async methods exist and are awaitable."""
    # Setup mock client to allow instantiation of the stream object.
    mock_rpc = mock.Mock(name="rpc")
    mock_transport = mock.Mock(name="transport")
    mock_transport.bidi_read_object = "bidi_read_object_key"
    mock_transport._wrapped_methods = {"bidi_read_object_key": mock_rpc}
    mock_gapic_client = mock.Mock(name="gapic_client")
    mock_gapic_client._transport = mock_transport
    mock_client = mock.Mock(name="client")
    mock_client._client = mock_gapic_client

    stream = _AsyncReadObjectStream(mock_client)

    # These methods are currently empty, but we can test they are awaitable
    # and don't raise exceptions.
    try:
        await stream.open()
        await stream.close()
        await stream.send(mock.Mock())
        await stream.recv()
    except Exception as e:
        pytest.fail(f"Async methods should be awaitable without errors. Raised: {e}")
