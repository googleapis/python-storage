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


def _make_credentials():
    creds = mock.Mock(spec=Credentials)
    creds.universe_domain = "googleapis.com"
    return creds


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="Async Client requires Python 3.10+ due to google-auth-library asyncio support",
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

        # We mock AsyncJSONConnection to prevent network logic during init
        with mock.patch(
            "google.cloud.storage._experimental.asyncio.async_client.AsyncJSONConnection"
        ) as MockConn:
            client = self._make_one(project=PROJECT, credentials=credentials)

            assert client.project == PROJECT

            # It is the instance of the Mock
            assert isinstance(client._json_connection, mock.Mock)
            assert client._json_connection == MockConn.return_value
            MockConn.assert_called_once_with(
                client,
                _async_http=None,
                credentials=client.credentials,
                client_info=None,
                api_endpoint=None,
            )

    def test_ctor_mtls_raises_error(self):
        credentials = _make_credentials()

        # Simulate environment where mTLS is enabled
        with mock.patch(
            "google.cloud.storage.abstracts.base_client.BaseClient._use_client_cert",
            new_callable=mock.PropertyMock,
        ) as mock_mtls:
            mock_mtls.return_value = True

            with pytest.raises(
                ValueError, match="Async Client currently do not support mTLS"
            ):
                self._make_one(credentials=credentials)

    def test_ctor_w_async_http_passed(self):
        credentials = _make_credentials()
        async_http = mock.Mock()

        with mock.patch(
            "google.cloud.storage._experimental.asyncio.async_client.AsyncJSONConnection"
        ) as MockConn:
            client = self._make_one(
                project="PROJECT", credentials=credentials, _async_http=async_http
            )

            client._json_connection
            MockConn.assert_called_once_with(
                client,
                _async_http=async_http,
                credentials=client.credentials,
                client_info=None,
                api_endpoint=None,
            )

    def test_bucket_not_implemented(self):
        credentials = _make_credentials()
        with mock.patch(
            "google.cloud.storage._experimental.asyncio.async_client.AsyncJSONConnection"
        ):
            client = self._make_one(project="PROJECT", credentials=credentials)

        with pytest.raises(NotImplementedError):
            client.bucket("my-bucket")
