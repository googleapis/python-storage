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
from unittest import mock
from google.auth import credentials as auth_credentials


class TestAsyncGrpcClient(unittest.TestCase):
    @mock.patch("google.cloud.storage_v2.StorageAsyncClient")
    def test_constructor_defaults_to_cloudpath(self, mock_async_storage_client):
        from google.cloud.storage._experimental import async_grpc_client

        mock_transport_cls = mock.MagicMock()
        mock_async_storage_client.get_transport_class.return_value = mock_transport_cls
        mock_creds = mock.Mock(spec=auth_credentials.Credentials)

        async_grpc_client.AsyncGrpcClient(credentials=mock_creds)

        mock_transport_cls.assert_called_once_with(
            credentials=mock_creds, attempt_direct_path=False
        )

    @mock.patch("google.cloud.storage_v2.StorageAsyncClient")
    def test_constructor_respects_directpath_true(self, mock_async_storage_client):
        from google.cloud.storage._experimental import async_grpc_client

        mock_transport_cls = mock.MagicMock()
        mock_async_storage_client.get_transport_class.return_value = mock_transport_cls
        mock_creds = mock.Mock(spec=auth_credentials.Credentials)

        async_grpc_client.AsyncGrpcClient(
            credentials=mock_creds, attempt_direct_path=True
        )

        mock_transport_cls.assert_called_once_with(
            credentials=mock_creds, attempt_direct_path=True
        )
