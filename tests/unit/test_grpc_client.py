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

class TestGrpcClient(unittest.TestCase):
    @mock.patch("google.cloud.client.ClientWithProject.__init__")
    @mock.patch("google.cloud.storage_v2.StorageClient")
    def test_constructor_passes_options_correctly(
        self, mock_storage_client, mock_base_client
    ):
        from google.cloud.storage import grpc_client

        mock_transport_cls = mock.MagicMock()
        mock_storage_client.get_transport_class.return_value = mock_transport_cls
        mock_creds = mock.Mock(spec=["_base", "_get_project_id"])
        mock_client_info = mock.Mock()
        client_options_dict = {"api_endpoint": "test.endpoint"}

        mock_base_instance = mock_base_client.return_value
        mock_base_instance._credentials = mock_creds

        client = grpc_client.GrpcClient(
            project="test-project",
            credentials=mock_creds,
            client_info=mock_client_info,
            client_options=client_options_dict,
        )

        # 1. Assert that the base class was initialized correctly.
        mock_base_client.assert_called_once_with(
            project="test-project", credentials=mock_creds
        )

        # 2. Assert DirectPath was configured.
        mock_storage_client.get_transport_class.assert_called_once_with("grpc")
        mock_transport_cls.create_channel.assert_called_once_with(
            attempt_direct_path=True
        )

        # 3. Assert the GAPIC client was created with the correct options.
        mock_storage_client.assert_called_once()
        _, kwargs = mock_storage_client.call_args
        self.assertEqual(kwargs["credentials"], mock_creds)
        self.assertEqual(kwargs["client_info"], mock_client_info)
        self.assertEqual(kwargs["client_options"], client_options_dict)

        # 4. Assert the client instance holds the mocked GAPIC client.
        self.assertIs(client._grpc_client, mock_storage_client.return_value)

    @mock.patch("google.cloud.storage.grpc_client.ClientWithProject")
    @mock.patch("google.cloud.storage_v2.StorageClient")
    def test_constructor_handles_api_key(self, mock_storage_client, mock_base_client):
        from google.cloud.storage import grpc_client

        mock_transport_cls = mock.MagicMock()
        mock_storage_client.get_transport_class.return_value = mock_transport_cls
        mock_creds = mock.Mock(spec=auth_credentials.Credentials)
        mock_creds.project_id = None

        mock_base_instance = mock_base_client.return_value
        mock_base_instance._credentials = mock_creds

        # Instantiate with just the api_key.
        grpc_client.GrpcClient(
            project="test-project",
            credentials=mock_creds,
            api_key="test-api-key"
        )

        # Assert that the GAPIC client was called with client_options
        # that contains the api_key.
        _, kwargs = mock_storage_client.call_args
        self.assertEqual(kwargs["client_options"]["api_key"], "test-api-key")
