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

from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    MultiRangeDownloader,
)


@pytest.fixture
def mock_async_grpc_client():
    """A mock for the AsyncGrpcClient."""
    return mock.Mock(name="AsyncGrpcClient")


@pytest.fixture
def mock_async_read_object_stream():
    """A mock for the _AsyncReadObjectStream class."""
    with mock.patch(
        "google.cloud.storage._experimental.asyncio.async_multi_range_downloader._AsyncReadObjectStream"
    ) as mock_stream_cls:
        mock_instance = mock.AsyncMock()
        mock_instance.generation_number = 12345
        mock_instance.read_handle = b"test-read-handle"
        mock_stream_cls.return_value = mock_instance
        yield mock_stream_cls


def test_init(mock_async_grpc_client):
    """Test the constructor of MultiRangeDownloader."""
    client = mock_async_grpc_client
    bucket_name = "test-bucket"
    object_name = "test-object"
    generation = 123
    read_handle = b"test-handle"

    mrd = MultiRangeDownloader(
        client,
        bucket_name=bucket_name,
        object_name=object_name,
        generation_number=generation,
        read_handle=read_handle,
    )

    assert mrd.client is client
    assert mrd.bucket_name == bucket_name
    assert mrd.object_name == object_name
    assert mrd.generation_number == generation
    assert mrd.read_handle == read_handle
    assert not hasattr(mrd, "read_obj_str")


@pytest.mark.asyncio
async def test_open(mock_async_grpc_client, mock_async_read_object_stream):
    """Test the open() method."""
    client = mock_async_grpc_client
    bucket_name = "test-bucket"
    object_name = "test-object"

    mrd = MultiRangeDownloader(
        client,
        bucket_name=bucket_name,
        object_name=object_name,
    )

    await mrd.open()

    mock_async_read_object_stream.assert_called_once_with(
        client=client,
        bucket_name=bucket_name,
        object_name=object_name,
        generation_number=None,
        read_handle=None,
    )

    mock_stream_instance = mock_async_read_object_stream.return_value
    mock_stream_instance.open.assert_awaited_once()

    assert mrd.read_obj_str is mock_stream_instance
    assert mrd.generation_number == mock_stream_instance.generation_number
    assert mrd.read_handle == mock_stream_instance.read_handle


@pytest.mark.asyncio
async def test_open_with_generation(
    mock_async_grpc_client, mock_async_read_object_stream
):
    """Test open() when generation_number is already set."""
    client = mock_async_grpc_client
    bucket_name = "test-bucket"
    object_name = "test-object"
    initial_generation = 456

    mrd = MultiRangeDownloader(
        client,
        bucket_name=bucket_name,
        object_name=object_name,
        generation_number=initial_generation,
    )

    # The mock stream will have a different generation number to ensure we don't overwrite it.
    mock_async_read_object_stream.return_value.generation_number = 789

    await mrd.open()

    mock_async_read_object_stream.assert_called_once_with(
        client=client,
        bucket_name=bucket_name,
        object_name=object_name,
        generation_number=initial_generation,
        read_handle=None,
    )

    mock_stream_instance = mock_async_read_object_stream.return_value
    mock_stream_instance.open.assert_awaited_once()

    assert mrd.read_obj_str is mock_stream_instance
    assert mrd.generation_number == initial_generation  # Should not be overwritten
    assert mrd.read_handle == mock_stream_instance.read_handle


@pytest.mark.asyncio
async def test_create_mrd(mock_async_grpc_client):
    """Test the create_mrd() factory method."""
    with mock.patch(
        "google.cloud.storage._experimental.asyncio.async_multi_range_downloader.MultiRangeDownloader.open",
        new_callable=mock.AsyncMock,
    ) as mock_open:
        client = mock_async_grpc_client
        bucket_name = "test-bucket"
        object_name = "test-object"
        generation = 123

        mrd = await MultiRangeDownloader.create_mrd(
            client, bucket_name, object_name, generation_number=generation
        )

        assert isinstance(mrd, MultiRangeDownloader)
        assert mrd.client is client
        assert mrd.bucket_name == bucket_name
        assert mrd.object_name == object_name
        assert mrd.generation_number == generation
        mock_open.assert_awaited_once()


def test_create_mrd_from_read_handle(mock_async_grpc_client):
    """Test that create_mrd_from_read_handle() raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        MultiRangeDownloader.create_mrd_from_read_handle(
            mock_async_grpc_client, b"handle"
        )


@pytest.mark.asyncio
async def test_download_ranges(mock_async_grpc_client):
    """Test that download_ranges() raises NotImplementedError."""
    mrd = MultiRangeDownloader(mock_async_grpc_client)
    with pytest.raises(NotImplementedError):
        await mrd.download_ranges([(0, 100)])
