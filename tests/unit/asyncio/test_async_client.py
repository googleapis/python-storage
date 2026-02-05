# Copyright 2026 Google LLC
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

import mock
import sys
import pytest
from google.auth.credentials import Credentials
from google.cloud.storage._experimental.asyncio.async_client import AsyncClient
from google.cloud.storage._experimental.asyncio.async_helpers import AsyncHTTPIterator

# Aliases to match sync test style
_marker = object()


def _make_credentials():
    creds = mock.Mock(spec=Credentials)
    creds.universe_domain = "googleapis.com"
    return creds


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="Async Client requires Python 3.10+ due to google-auth-library asyncio support"
)
class TestAsyncClient:
    @staticmethod
    def _get_target_class():
        return AsyncClient

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_ctor_defaults(self):
        PROJECT = "PROJECT"
        credentials = _make_credentials()

        # We mock AsyncConnection to prevent network logic during init
        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection") as MockConn:
            client = self._make_one(project=PROJECT, credentials=credentials)

        assert client.project == PROJECT
        # It is the instance of the Mock
        assert isinstance(client._connection, mock.Mock)
        assert client._connection == MockConn.return_value

        # Verify specific async attributes
        assert client._async_http_internal is None
        assert client._async_http_passed_by_user is False

        # Verify inheritance from BaseClient worked (batch stack, etc)
        assert client.current_batch is None
        assert list(client._batch_stack) == []

    def test_ctor_mtls_raises_error(self):
        credentials = _make_credentials()

        # Simulate environment where mTLS is enabled
        with mock.patch("google.cloud.storage.abstracts.base_client.BaseClient._use_client_cert", new_callable=mock.PropertyMock) as mock_mtls:
            mock_mtls.return_value = True

            with pytest.raises(ValueError, match="Async Client currently do not support mTLS"):
                self._make_one(credentials=credentials)

    def test_ctor_w_async_http_passed(self):
        credentials = _make_credentials()
        async_http = mock.Mock()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(
                project="PROJECT",
                credentials=credentials,
                _async_http=async_http
            )

        assert client._async_http_internal is async_http
        assert client._async_http_passed_by_user is True

    def test_async_http_property_creates_session(self):
        credentials = _make_credentials()
        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        assert client._async_http_internal is None

        # Mock the auth session class
        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncSession") as MockSession:
            session = client.async_http

            assert session is MockSession.return_value
            assert client._async_http_internal is session
            # Should be initialized with the AsyncCredsWrapper, not the raw credentials
            MockSession.assert_called_once()
            call_kwargs = MockSession.call_args[1]
            assert call_kwargs['credentials'] == client.credentials

    @pytest.mark.asyncio
    async def test_close_manages_session_lifecycle(self):
        credentials = _make_credentials()
        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        # 1. Internal session created by client -> Client closes it
        mock_internal = mock.AsyncMock()
        client._async_http_internal = mock_internal
        client._async_http_passed_by_user = False

        await client.close()
        mock_internal.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_ignores_user_session(self):
        credentials = _make_credentials()
        user_session = mock.AsyncMock()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(
                project="PROJECT",
                credentials=credentials,
                _async_http=user_session
            )

        # 2. External session passed by user -> Client DOES NOT close it
        await client.close()
        user_session.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_resource(self):
        path = "/b/bucket"
        query_params = {"foo": "bar"}
        credentials = _make_credentials()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        # Mock the connection's api_request
        client._connection.api_request = mock.AsyncMock(
            return_value="response")

        result = await client._get_resource(path, query_params=query_params)

        assert result == "response"
        client._connection.api_request.assert_awaited_once_with(
            method="GET",
            path=path,
            query_params=query_params,
            headers=None,
            timeout=mock.ANY,
            retry=mock.ANY,
            _target_object=None
        )

    @pytest.mark.asyncio
    async def test_list_resource(self):
        path = "/b/bucket/o"
        item_to_value = mock.Mock()
        credentials = _make_credentials()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        iterator = client._list_resource(
            path=path,
            item_to_value=item_to_value,
            max_results=10,
            page_token="token"
        )

        assert isinstance(iterator, AsyncHTTPIterator)
        assert iterator.path == path
        assert iterator.max_results == 10

    @pytest.mark.asyncio
    async def test_patch_resource(self):
        path = "/b/bucket"
        data = {"key": "val"}
        credentials = _make_credentials()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        client._connection.api_request = mock.AsyncMock()

        await client._patch_resource(path, data=data)

        client._connection.api_request.assert_awaited_once_with(
            method="PATCH",
            path=path,
            data=data,
            query_params=None,
            headers=None,
            timeout=mock.ANY,
            retry=None,
            _target_object=None
        )

    @pytest.mark.asyncio
    async def test_put_resource(self):
        path = "/b/bucket/o/obj"
        data = b"bytes"
        credentials = _make_credentials()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        client._connection.api_request = mock.AsyncMock()

        await client._put_resource(path, data=data)

        client._connection.api_request.assert_awaited_once_with(
            method="PUT",
            path=path,
            data=data,
            query_params=None,
            headers=None,
            timeout=mock.ANY,
            retry=None,
            _target_object=None
        )

    @pytest.mark.asyncio
    async def test_post_resource(self):
        path = "/b/bucket/o/obj/compose"
        data = {"source": []}
        credentials = _make_credentials()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        client._connection.api_request = mock.AsyncMock()

        await client._post_resource(path, data=data)

        client._connection.api_request.assert_awaited_once_with(
            method="POST",
            path=path,
            data=data,
            query_params=None,
            headers=None,
            timeout=mock.ANY,
            retry=None,
            _target_object=None
        )

    @pytest.mark.asyncio
    async def test_delete_resource(self):
        path = "/b/bucket"
        credentials = _make_credentials()

        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        client._connection.api_request = mock.AsyncMock()

        await client._delete_resource(path)

        client._connection.api_request.assert_awaited_once_with(
            method="DELETE",
            path=path,
            query_params=None,
            headers=None,
            timeout=mock.ANY,
            retry=mock.ANY,
            _target_object=None
        )

    def test_bucket_not_implemented(self):
        credentials = _make_credentials()
        with mock.patch("google.cloud.storage._experimental.asyncio.async_client.AsyncConnection"):
            client = self._make_one(project="PROJECT", credentials=credentials)

        with pytest.raises(NotImplementedError):
            client.bucket("my-bucket")
