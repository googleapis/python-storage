# Copyright 2015 Google LLC
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
import json
import unittest

import mock
import pytest
import requests
from six.moves import http_client


def _make_credentials():
    import google.auth.credentials

    return mock.Mock(spec=google.auth.credentials.Credentials)


def _create_signing_credentials():
    import google.auth.credentials

    class _SigningCredentials(
        google.auth.credentials.Credentials, google.auth.credentials.Signing
    ):
        pass

    credentials = mock.Mock(spec=_SigningCredentials)

    return credentials


def _make_connection(*responses):
    import google.cloud.storage._http
    from google.cloud.exceptions import NotFound

    mock_conn = mock.create_autospec(google.cloud.storage._http.Connection)
    mock_conn.user_agent = "testing 1.2.3"
    mock_conn.api_request.side_effect = list(responses) + [NotFound("miss")]
    return mock_conn


def _make_response(status=http_client.OK, content=b"", headers={}):
    response = requests.Response()
    response.status_code = status
    response._content = content
    response.headers = headers
    response.request = requests.Request()
    return response


def _make_json_response(data, status=http_client.OK, headers=None):
    headers = headers or {}
    headers["Content-Type"] = "application/json"
    return _make_response(
        status=status, content=json.dumps(data).encode("utf-8"), headers=headers
    )


def _make_requests_session(responses):
    session = mock.create_autospec(requests.Session, instance=True)
    session.request.side_effect = responses
    return session


class TestClient(unittest.TestCase):
    @staticmethod
    def _get_target_class():
        from google.cloud.storage.client import Client

        return Client

    @staticmethod
    def _get_default_timeout():
        from google.cloud.storage.constants import _DEFAULT_TIMEOUT

        return _DEFAULT_TIMEOUT

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_ctor_connection_type(self):
        from google.cloud._http import ClientInfo
        from google.cloud.storage._http import Connection

        PROJECT = "PROJECT"
        credentials = _make_credentials()

        client = self._make_one(project=PROJECT, credentials=credentials)

        self.assertEqual(client.project, PROJECT)
        self.assertIsInstance(client._connection, Connection)
        self.assertIs(client._connection.credentials, credentials)
        self.assertIsNone(client.current_batch)
        self.assertEqual(list(client._batch_stack), [])
        self.assertIsInstance(client._connection._client_info, ClientInfo)
        self.assertEqual(
            client._connection.API_BASE_URL, Connection.DEFAULT_API_ENDPOINT
        )

    def test_ctor_w_empty_client_options(self):
        from google.api_core.client_options import ClientOptions

        PROJECT = "PROJECT"
        credentials = _make_credentials()
        client_options = ClientOptions()

        client = self._make_one(
            project=PROJECT, credentials=credentials, client_options=client_options
        )

        self.assertEqual(
            client._connection.API_BASE_URL, client._connection.DEFAULT_API_ENDPOINT
        )

    def test_ctor_w_client_options_dict(self):

        PROJECT = "PROJECT"
        credentials = _make_credentials()
        client_options = {"api_endpoint": "https://www.foo-googleapis.com"}

        client = self._make_one(
            project=PROJECT, credentials=credentials, client_options=client_options
        )

        self.assertEqual(
            client._connection.API_BASE_URL, "https://www.foo-googleapis.com"
        )

    def test_ctor_w_client_options_object(self):
        from google.api_core.client_options import ClientOptions

        PROJECT = "PROJECT"
        credentials = _make_credentials()
        client_options = ClientOptions(api_endpoint="https://www.foo-googleapis.com")

        client = self._make_one(
            project=PROJECT, credentials=credentials, client_options=client_options
        )

        self.assertEqual(
            client._connection.API_BASE_URL, "https://www.foo-googleapis.com"
        )

    def test_ctor_wo_project(self):
        from google.cloud.storage._http import Connection

        PROJECT = "PROJECT"
        credentials = _make_credentials()

        ddp_patch = mock.patch(
            "google.cloud.client._determine_default_project", return_value=PROJECT
        )

        with ddp_patch:
            client = self._make_one(credentials=credentials)

        self.assertEqual(client.project, PROJECT)
        self.assertIsInstance(client._connection, Connection)
        self.assertIs(client._connection.credentials, credentials)
        self.assertIsNone(client.current_batch)
        self.assertEqual(list(client._batch_stack), [])

    def test_ctor_w_project_explicit_none(self):
        from google.cloud.storage._http import Connection

        credentials = _make_credentials()

        client = self._make_one(project=None, credentials=credentials)

        self.assertIsNone(client.project)
        self.assertIsInstance(client._connection, Connection)
        self.assertIs(client._connection.credentials, credentials)
        self.assertIsNone(client.current_batch)
        self.assertEqual(list(client._batch_stack), [])

    def test_ctor_w_client_info(self):
        from google.cloud._http import ClientInfo
        from google.cloud.storage._http import Connection

        credentials = _make_credentials()
        client_info = ClientInfo()

        client = self._make_one(
            project=None, credentials=credentials, client_info=client_info
        )

        self.assertIsNone(client.project)
        self.assertIsInstance(client._connection, Connection)
        self.assertIs(client._connection.credentials, credentials)
        self.assertIsNone(client.current_batch)
        self.assertEqual(list(client._batch_stack), [])
        self.assertIs(client._connection._client_info, client_info)

    def test_create_anonymous_client(self):
        from google.auth.credentials import AnonymousCredentials
        from google.cloud.storage._http import Connection

        klass = self._get_target_class()
        client = klass.create_anonymous_client()

        self.assertIsNone(client.project)
        self.assertIsInstance(client._connection, Connection)
        self.assertIsInstance(client._connection.credentials, AnonymousCredentials)

    def test__push_batch_and__pop_batch(self):
        from google.cloud.storage.batch import Batch

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        batch1 = Batch(client)
        batch2 = Batch(client)
        client._push_batch(batch1)
        self.assertEqual(list(client._batch_stack), [batch1])
        self.assertIs(client.current_batch, batch1)
        client._push_batch(batch2)
        self.assertIs(client.current_batch, batch2)
        # list(_LocalStack) returns in reverse order.
        self.assertEqual(list(client._batch_stack), [batch2, batch1])
        self.assertIs(client._pop_batch(), batch2)
        self.assertEqual(list(client._batch_stack), [batch1])
        self.assertIs(client._pop_batch(), batch1)
        self.assertEqual(list(client._batch_stack), [])

    def test__connection_setter(self):
        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        client._base_connection = None  # Unset the value from the constructor
        client._connection = connection = object()
        self.assertIs(client._base_connection, connection)

    def test__connection_setter_when_set(self):
        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        self.assertRaises(ValueError, setattr, client, "_connection", None)

    def test__connection_getter_no_batch(self):
        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        self.assertIs(client._connection, client._base_connection)
        self.assertIsNone(client.current_batch)

    def test__connection_getter_with_batch(self):
        from google.cloud.storage.batch import Batch

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        batch = Batch(client)
        client._push_batch(batch)
        self.assertIsNot(client._connection, client._base_connection)
        self.assertIs(client._connection, batch)
        self.assertIs(client.current_batch, batch)

    def test_get_service_account_email_wo_project(self):
        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        EMAIL = "storage-user-123@example.com"
        RESOURCE = {"kind": "storage#serviceAccount", "email_address": EMAIL}

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        http = _make_requests_session([_make_json_response(RESOURCE)])
        client._http_internal = http

        service_account_email = client.get_service_account_email(timeout=42)

        self.assertEqual(service_account_email, EMAIL)
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "projects/%s/serviceAccount" % (PROJECT,),
            ]
        )
        http.request.assert_called_once_with(
            method="GET", url=URI, data=None, headers=mock.ANY, timeout=42
        )

    def test_get_service_account_email_w_project(self):
        PROJECT = "PROJECT"
        OTHER_PROJECT = "OTHER_PROJECT"
        CREDENTIALS = _make_credentials()
        EMAIL = "storage-user-123@example.com"
        RESOURCE = {"kind": "storage#serviceAccount", "email_address": EMAIL}

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        http = _make_requests_session([_make_json_response(RESOURCE)])
        client._http_internal = http

        service_account_email = client.get_service_account_email(project=OTHER_PROJECT)

        self.assertEqual(service_account_email, EMAIL)
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "projects/%s/serviceAccount" % (OTHER_PROJECT,),
            ]
        )
        http.request.assert_called_once_with(
            method="GET",
            url=URI,
            data=None,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_bucket(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        BUCKET_NAME = "BUCKET_NAME"

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        bucket = client.bucket(BUCKET_NAME)
        self.assertIsInstance(bucket, Bucket)
        self.assertIs(bucket.client, client)
        self.assertEqual(bucket.name, BUCKET_NAME)
        self.assertIsNone(bucket.user_project)

    def test_bucket_w_user_project(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = "PROJECT"
        USER_PROJECT = "USER_PROJECT"
        CREDENTIALS = _make_credentials()
        BUCKET_NAME = "BUCKET_NAME"

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        bucket = client.bucket(BUCKET_NAME, user_project=USER_PROJECT)
        self.assertIsInstance(bucket, Bucket)
        self.assertIs(bucket.client, client)
        self.assertEqual(bucket.name, BUCKET_NAME)
        self.assertEqual(bucket.user_project, USER_PROJECT)

    def test_batch(self):
        from google.cloud.storage.batch import Batch

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        batch = client.batch()
        self.assertIsInstance(batch, Batch)
        self.assertIs(batch._client, client)

    def test_get_bucket_with_string_miss(self):
        from google.cloud.exceptions import NotFound

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        NONESUCH = "nonesuch"
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
                "nonesuch?projection=noAcl",
            ]
        )
        http = _make_requests_session(
            [_make_json_response({}, status=http_client.NOT_FOUND)]
        )
        client._http_internal = http

        with self.assertRaises(NotFound):
            client.get_bucket(NONESUCH, timeout=42)

        http.request.assert_called_once_with(
            method="GET", url=URI, data=mock.ANY, headers=mock.ANY, timeout=42
        )

    def test_get_bucket_with_string_hit(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        BUCKET_NAME = "bucket-name"
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
                "%s?projection=noAcl" % (BUCKET_NAME,),
            ]
        )

        data = {"name": BUCKET_NAME}
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http

        bucket = client.get_bucket(BUCKET_NAME)

        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, BUCKET_NAME)
        http.request.assert_called_once_with(
            method="GET",
            url=URI,
            data=mock.ANY,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_get_bucket_with_object_miss(self):
        from google.cloud.exceptions import NotFound
        from google.cloud.storage.bucket import Bucket

        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)

        nonesuch = "nonesuch"
        bucket_obj = Bucket(client, nonesuch)
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
                "nonesuch?projection=noAcl",
            ]
        )
        http = _make_requests_session(
            [_make_json_response({}, status=http_client.NOT_FOUND)]
        )
        client._http_internal = http

        with self.assertRaises(NotFound):
            client.get_bucket(bucket_obj)

        http.request.assert_called_once_with(
            method="GET",
            url=URI,
            data=mock.ANY,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_get_bucket_with_object_hit(self):
        from google.cloud.storage.bucket import Bucket

        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)

        bucket_name = "bucket-name"
        bucket_obj = Bucket(client, bucket_name)
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
                "%s?projection=noAcl" % (bucket_name,),
            ]
        )

        data = {"name": bucket_name}
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http

        bucket = client.get_bucket(bucket_obj)

        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, bucket_name)
        http.request.assert_called_once_with(
            method="GET",
            url=URI,
            data=mock.ANY,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_lookup_bucket_miss(self):
        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        NONESUCH = "nonesuch"
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
                "nonesuch?projection=noAcl",
            ]
        )
        http = _make_requests_session(
            [_make_json_response({}, status=http_client.NOT_FOUND)]
        )
        client._http_internal = http

        bucket = client.lookup_bucket(NONESUCH, timeout=42)

        self.assertIsNone(bucket)
        http.request.assert_called_once_with(
            method="GET", url=URI, data=mock.ANY, headers=mock.ANY, timeout=42
        )

    def test_lookup_bucket_hit(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        BUCKET_NAME = "bucket-name"
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
                "%s?projection=noAcl" % (BUCKET_NAME,),
            ]
        )
        data = {"name": BUCKET_NAME}
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http

        bucket = client.lookup_bucket(BUCKET_NAME)

        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, BUCKET_NAME)
        http.request.assert_called_once_with(
            method="GET",
            url=URI,
            data=mock.ANY,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_create_bucket_w_missing_client_project(self):
        credentials = _make_credentials()
        client = self._make_one(project=None, credentials=credentials)

        with self.assertRaises(ValueError):
            client.create_bucket("bucket")

    def test_create_bucket_w_conflict(self):
        from google.cloud.exceptions import Conflict

        project = "PROJECT"
        user_project = "USER_PROJECT"
        other_project = "OTHER_PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        connection = _make_connection()
        client._base_connection = connection
        connection.api_request.side_effect = Conflict("testing")

        bucket_name = "bucket-name"
        data = {"name": bucket_name}

        with self.assertRaises(Conflict):
            client.create_bucket(
                bucket_name, project=other_project, user_project=user_project
            )

        connection.api_request.assert_called_once_with(
            method="POST",
            path="/b",
            query_params={"project": other_project, "userProject": user_project},
            data=data,
            _target_object=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    @mock.patch("warnings.warn")
    def test_create_requester_pays_deprecated(self, mock_warn):
        from google.cloud.storage.bucket import Bucket

        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        bucket_name = "bucket-name"
        json_expected = {"name": bucket_name, "billing": {"requesterPays": True}}
        http = _make_requests_session([_make_json_response(json_expected)])
        client._http_internal = http

        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b?project=%s" % (project,),
            ]
        )

        bucket = client.create_bucket(bucket_name, requester_pays=True)

        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, bucket_name)
        self.assertTrue(bucket.requester_pays)
        http.request.assert_called_once_with(
            method="POST", url=URI, data=mock.ANY, headers=mock.ANY, timeout=mock.ANY
        )
        json_sent = http.request.call_args_list[0][1]["data"]
        self.assertEqual(json_expected, json.loads(json_sent))

        mock_warn.assert_called_with(
            "requester_pays arg is deprecated. Use Bucket().requester_pays instead.",
            PendingDeprecationWarning,
            stacklevel=1,
        )

    def test_create_bucket_w_predefined_acl_invalid(self):
        project = "PROJECT"
        bucket_name = "bucket-name"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)

        with self.assertRaises(ValueError):
            client.create_bucket(bucket_name, predefined_acl="bogus")

    def test_create_bucket_w_predefined_acl_valid(self):
        project = "PROJECT"
        bucket_name = "bucket-name"
        data = {"name": bucket_name}

        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        connection = _make_connection(data)
        client._base_connection = connection
        bucket = client.create_bucket(
            bucket_name, predefined_acl="publicRead", timeout=42
        )

        connection.api_request.assert_called_once_with(
            method="POST",
            path="/b",
            query_params={"project": project, "predefinedAcl": "publicRead"},
            data=data,
            _target_object=bucket,
            timeout=42,
        )

    def test_create_bucket_w_predefined_default_object_acl_invalid(self):
        project = "PROJECT"
        bucket_name = "bucket-name"

        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)

        with self.assertRaises(ValueError):
            client.create_bucket(bucket_name, predefined_default_object_acl="bogus")

    def test_create_bucket_w_predefined_default_object_acl_valid(self):
        project = "PROJECT"
        bucket_name = "bucket-name"
        data = {"name": bucket_name}

        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        connection = _make_connection(data)
        client._base_connection = connection
        bucket = client.create_bucket(
            bucket_name, predefined_default_object_acl="publicRead"
        )

        connection.api_request.assert_called_once_with(
            method="POST",
            path="/b",
            query_params={
                "project": project,
                "predefinedDefaultObjectAcl": "publicRead",
            },
            data=data,
            _target_object=bucket,
            timeout=self._get_default_timeout(),
        )

    def test_create_bucket_w_explicit_location(self):
        project = "PROJECT"
        bucket_name = "bucket-name"
        location = "us-central1"
        data = {"location": location, "name": bucket_name}

        connection = _make_connection(
            data, "{'location': 'us-central1', 'name': 'bucket-name'}"
        )

        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        client._base_connection = connection

        bucket = client.create_bucket(bucket_name, location=location)

        connection.api_request.assert_called_once_with(
            method="POST",
            path="/b",
            data=data,
            _target_object=bucket,
            query_params={"project": project},
            timeout=self._get_default_timeout(),
        )
        self.assertEqual(bucket.location, location)

    def test_create_bucket_w_explicit_project(self):
        from google.cloud.storage.client import Client

        PROJECT = "PROJECT"
        OTHER_PROJECT = "other-project-123"
        BUCKET_NAME = "bucket-name"
        DATA = {"name": BUCKET_NAME}
        connection = _make_connection(DATA)

        client = Client(project=PROJECT)
        client._base_connection = connection

        bucket = client.create_bucket(BUCKET_NAME, project=OTHER_PROJECT)
        connection.api_request.assert_called_once_with(
            method="POST",
            path="/b",
            query_params={"project": OTHER_PROJECT},
            data=DATA,
            _target_object=bucket,
            timeout=self._get_default_timeout(),
        )

    def test_create_w_extra_properties(self):
        from google.cloud.storage.client import Client
        from google.cloud.storage.bucket import Bucket

        BUCKET_NAME = "bucket-name"
        PROJECT = "PROJECT"
        CORS = [
            {
                "maxAgeSeconds": 60,
                "methods": ["*"],
                "origin": ["https://example.com/frontend"],
                "responseHeader": ["X-Custom-Header"],
            }
        ]
        LIFECYCLE_RULES = [{"action": {"type": "Delete"}, "condition": {"age": 365}}]
        LOCATION = "eu"
        LABELS = {"color": "red", "flavor": "cherry"}
        STORAGE_CLASS = "NEARLINE"
        DATA = {
            "name": BUCKET_NAME,
            "cors": CORS,
            "lifecycle": {"rule": LIFECYCLE_RULES},
            "location": LOCATION,
            "storageClass": STORAGE_CLASS,
            "versioning": {"enabled": True},
            "billing": {"requesterPays": True},
            "labels": LABELS,
        }

        connection = _make_connection(DATA)
        client = Client(project=PROJECT)
        client._base_connection = connection

        bucket = Bucket(client=client, name=BUCKET_NAME)
        bucket.cors = CORS
        bucket.lifecycle_rules = LIFECYCLE_RULES
        bucket.storage_class = STORAGE_CLASS
        bucket.versioning_enabled = True
        bucket.requester_pays = True
        bucket.labels = LABELS
        client.create_bucket(bucket, location=LOCATION)

        connection.api_request.assert_called_once_with(
            method="POST",
            path="/b",
            query_params={"project": PROJECT},
            data=DATA,
            _target_object=bucket,
            timeout=self._get_default_timeout(),
        )

    def test_create_hit(self):
        from google.cloud.storage.client import Client

        PROJECT = "PROJECT"
        BUCKET_NAME = "bucket-name"
        DATA = {"name": BUCKET_NAME}
        connection = _make_connection(DATA)
        client = Client(project=PROJECT)
        client._base_connection = connection

        bucket = client.create_bucket(BUCKET_NAME)

        connection.api_request.assert_called_once_with(
            method="POST",
            path="/b",
            query_params={"project": PROJECT},
            data=DATA,
            _target_object=bucket,
            timeout=self._get_default_timeout(),
        )

    def test_create_bucket_w_string_success(self):
        from google.cloud.storage.bucket import Bucket

        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)

        bucket_name = "bucket-name"
        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b?project=%s" % (project,),
            ]
        )
        json_expected = {"name": bucket_name}
        data = json_expected
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http

        bucket = client.create_bucket(bucket_name)

        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, bucket_name)
        http.request.assert_called_once_with(
            method="POST", url=URI, data=mock.ANY, headers=mock.ANY, timeout=mock.ANY
        )
        json_sent = http.request.call_args_list[0][1]["data"]
        self.assertEqual(json_expected, json.loads(json_sent))

    def test_create_bucket_w_object_success(self):
        from google.cloud.storage.bucket import Bucket

        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)

        bucket_name = "bucket-name"
        bucket_obj = Bucket(client, bucket_name)
        bucket_obj.storage_class = "COLDLINE"
        bucket_obj.requester_pays = True

        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b?project=%s" % (project,),
            ]
        )
        json_expected = {
            "name": bucket_name,
            "billing": {"requesterPays": True},
            "storageClass": "COLDLINE",
        }
        data = json_expected
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http

        bucket = client.create_bucket(bucket_obj)

        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, bucket_name)
        self.assertTrue(bucket.requester_pays)
        http.request.assert_called_once_with(
            method="POST", url=URI, data=mock.ANY, headers=mock.ANY, timeout=mock.ANY
        )
        json_sent = http.request.call_args_list[0][1]["data"]
        self.assertEqual(json_expected, json.loads(json_sent))

    def test_download_blob_to_file_with_blob(self):
        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        blob = mock.Mock()
        file_obj = io.BytesIO()

        client.download_blob_to_file(blob, file_obj)
        blob.download_to_file.assert_called_once_with(
            file_obj, client=client, start=None, end=None
        )

    def test_download_blob_to_file_with_uri(self):
        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        blob = mock.Mock()
        file_obj = io.BytesIO()

        with mock.patch(
            "google.cloud.storage.client.Blob.from_string", return_value=blob
        ):
            client.download_blob_to_file("gs://bucket_name/path/to/object", file_obj)

        blob.download_to_file.assert_called_once_with(
            file_obj, client=client, start=None, end=None
        )

    def test_download_blob_to_file_with_invalid_uri(self):
        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        file_obj = io.BytesIO()

        with pytest.raises(ValueError, match="URI scheme must be gs"):
            client.download_blob_to_file("http://bucket_name/path/to/object", file_obj)

    def test_list_blobs(self):
        from google.cloud.storage.bucket import Bucket

        BUCKET_NAME = "bucket-name"

        credentials = _make_credentials()
        client = self._make_one(project="PROJECT", credentials=credentials)
        connection = _make_connection({"items": []})

        with mock.patch(
            "google.cloud.storage.client.Client._connection",
            new_callable=mock.PropertyMock,
        ) as client_mock:
            client_mock.return_value = connection

            bucket_obj = Bucket(client, BUCKET_NAME)
            iterator = client.list_blobs(bucket_obj)
            blobs = list(iterator)

            self.assertEqual(blobs, [])
            connection.api_request.assert_called_once_with(
                method="GET",
                path="/b/%s/o" % BUCKET_NAME,
                query_params={"projection": "noAcl"},
                timeout=self._get_default_timeout(),
            )

    def test_list_blobs_w_all_arguments_and_user_project(self):
        from google.cloud.storage.bucket import Bucket

        BUCKET_NAME = "name"
        USER_PROJECT = "user-project-123"
        MAX_RESULTS = 10
        PAGE_TOKEN = "ABCD"
        PREFIX = "subfolder"
        DELIMITER = "/"
        VERSIONS = True
        PROJECTION = "full"
        FIELDS = "items/contentLanguage,nextPageToken"
        EXPECTED = {
            "maxResults": 10,
            "pageToken": PAGE_TOKEN,
            "prefix": PREFIX,
            "delimiter": DELIMITER,
            "versions": VERSIONS,
            "projection": PROJECTION,
            "fields": FIELDS,
            "userProject": USER_PROJECT,
        }

        credentials = _make_credentials()
        client = self._make_one(project=USER_PROJECT, credentials=credentials)
        connection = _make_connection({"items": []})

        with mock.patch(
            "google.cloud.storage.client.Client._connection",
            new_callable=mock.PropertyMock,
        ) as client_mock:
            client_mock.return_value = connection

            bucket = Bucket(client, BUCKET_NAME, user_project=USER_PROJECT)
            iterator = client.list_blobs(
                bucket_or_name=bucket,
                max_results=MAX_RESULTS,
                page_token=PAGE_TOKEN,
                prefix=PREFIX,
                delimiter=DELIMITER,
                versions=VERSIONS,
                projection=PROJECTION,
                fields=FIELDS,
                timeout=42,
            )
            blobs = list(iterator)

            self.assertEqual(blobs, [])
            connection.api_request.assert_called_once_with(
                method="GET",
                path="/b/%s/o" % BUCKET_NAME,
                query_params=EXPECTED,
                timeout=42,
            )

    def test_list_buckets_wo_project(self):
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=None, credentials=CREDENTIALS)

        with self.assertRaises(ValueError):
            client.list_buckets()

    def test_list_buckets_empty(self):
        from six.moves.urllib.parse import parse_qs
        from six.moves.urllib.parse import urlparse

        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        http = _make_requests_session([_make_json_response({})])
        client._http_internal = http

        buckets = list(client.list_buckets())

        self.assertEqual(len(buckets), 0)

        http.request.assert_called_once_with(
            method="GET",
            url=mock.ANY,
            data=mock.ANY,
            headers=mock.ANY,
            timeout=mock.ANY,
        )

        requested_url = http.request.mock_calls[0][2]["url"]
        expected_base_url = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
            ]
        )
        self.assertTrue(requested_url.startswith(expected_base_url))

        expected_query = {"project": [PROJECT], "projection": ["noAcl"]}
        uri_parts = urlparse(requested_url)
        self.assertEqual(parse_qs(uri_parts.query), expected_query)

    def test_list_buckets_explicit_project(self):
        from six.moves.urllib.parse import parse_qs
        from six.moves.urllib.parse import urlparse

        PROJECT = "PROJECT"
        OTHER_PROJECT = "OTHER_PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        http = _make_requests_session([_make_json_response({})])
        client._http_internal = http

        buckets = list(client.list_buckets(project=OTHER_PROJECT))

        self.assertEqual(len(buckets), 0)

        http.request.assert_called_once_with(
            method="GET",
            url=mock.ANY,
            data=mock.ANY,
            headers=mock.ANY,
            timeout=mock.ANY,
        )

        requested_url = http.request.mock_calls[0][2]["url"]
        expected_base_url = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
            ]
        )
        self.assertTrue(requested_url.startswith(expected_base_url))

        expected_query = {"project": [OTHER_PROJECT], "projection": ["noAcl"]}
        uri_parts = urlparse(requested_url)
        self.assertEqual(parse_qs(uri_parts.query), expected_query)

    def test_list_buckets_non_empty(self):
        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        BUCKET_NAME = "bucket-name"

        data = {"items": [{"name": BUCKET_NAME}]}
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http

        buckets = list(client.list_buckets())

        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0].name, BUCKET_NAME)

        http.request.assert_called_once_with(
            method="GET",
            url=mock.ANY,
            data=mock.ANY,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_list_buckets_all_arguments(self):
        from six.moves.urllib.parse import parse_qs
        from six.moves.urllib.parse import urlparse

        PROJECT = "foo-bar"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        MAX_RESULTS = 10
        PAGE_TOKEN = "ABCD"
        PREFIX = "subfolder"
        PROJECTION = "full"
        FIELDS = "items/id,nextPageToken"

        data = {"items": []}
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http
        iterator = client.list_buckets(
            max_results=MAX_RESULTS,
            page_token=PAGE_TOKEN,
            prefix=PREFIX,
            projection=PROJECTION,
            fields=FIELDS,
            timeout=42,
        )
        buckets = list(iterator)
        self.assertEqual(buckets, [])
        http.request.assert_called_once_with(
            method="GET", url=mock.ANY, data=mock.ANY, headers=mock.ANY, timeout=42
        )

        requested_url = http.request.mock_calls[0][2]["url"]
        expected_base_url = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "b",
            ]
        )
        self.assertTrue(requested_url.startswith(expected_base_url))

        expected_query = {
            "project": [PROJECT],
            "maxResults": [str(MAX_RESULTS)],
            "pageToken": [PAGE_TOKEN],
            "prefix": [PREFIX],
            "projection": [PROJECTION],
            "fields": [FIELDS],
        }
        uri_parts = urlparse(requested_url)
        self.assertEqual(parse_qs(uri_parts.query), expected_query)

    def test_list_buckets_page_empty_response(self):
        from google.api_core import page_iterator

        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)
        iterator = client.list_buckets()
        page = page_iterator.Page(iterator, (), None)
        iterator._page = page
        self.assertEqual(list(page), [])

    def test_list_buckets_page_non_empty_response(self):
        import six
        from google.cloud.storage.bucket import Bucket

        project = "PROJECT"
        credentials = _make_credentials()
        client = self._make_one(project=project, credentials=credentials)

        blob_name = "bucket-name"
        response = {"items": [{"name": blob_name}]}

        def dummy_response():
            return response

        iterator = client.list_buckets()
        iterator._get_next_page_response = dummy_response

        page = six.next(iterator.pages)
        self.assertEqual(page.num_items, 1)
        bucket = six.next(page)
        self.assertEqual(page.remaining, 0)
        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, blob_name)

    def _create_hmac_key_helper(
        self, explicit_project=None, user_project=None, timeout=None
    ):
        import datetime
        from pytz import UTC
        from six.moves.urllib.parse import urlencode
        from google.cloud.storage.hmac_key import HMACKeyMetadata

        PROJECT = "PROJECT"
        ACCESS_ID = "ACCESS-ID"
        CREDENTIALS = _make_credentials()
        EMAIL = "storage-user-123@example.com"
        SECRET = "a" * 40
        now = datetime.datetime.utcnow().replace(tzinfo=UTC)
        now_stamp = "{}Z".format(now.isoformat())

        if explicit_project is not None:
            expected_project = explicit_project
        else:
            expected_project = PROJECT

        RESOURCE = {
            "kind": "storage#hmacKey",
            "metadata": {
                "accessId": ACCESS_ID,
                "etag": "ETAG",
                "id": "projects/{}/hmacKeys/{}".format(PROJECT, ACCESS_ID),
                "project": expected_project,
                "state": "ACTIVE",
                "serviceAccountEmail": EMAIL,
                "timeCreated": now_stamp,
                "updated": now_stamp,
            },
            "secret": SECRET,
        }

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        http = _make_requests_session([_make_json_response(RESOURCE)])
        client._http_internal = http

        kwargs = {}
        if explicit_project is not None:
            kwargs["project_id"] = explicit_project

        if user_project is not None:
            kwargs["user_project"] = user_project

        if timeout is None:
            timeout = self._get_default_timeout()
        kwargs["timeout"] = timeout

        metadata, secret = client.create_hmac_key(service_account_email=EMAIL, **kwargs)

        self.assertIsInstance(metadata, HMACKeyMetadata)
        self.assertIs(metadata._client, client)
        self.assertEqual(metadata._properties, RESOURCE["metadata"])
        self.assertEqual(secret, RESOURCE["secret"])

        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "projects",
                expected_project,
                "hmacKeys",
            ]
        )
        qs_params = {"serviceAccountEmail": EMAIL}

        if user_project is not None:
            qs_params["userProject"] = user_project

        FULL_URI = "{}?{}".format(URI, urlencode(qs_params))
        http.request.assert_called_once_with(
            method="POST", url=FULL_URI, data=None, headers=mock.ANY, timeout=timeout
        )

    def test_create_hmac_key_defaults(self):
        self._create_hmac_key_helper()

    def test_create_hmac_key_explicit_project(self):
        self._create_hmac_key_helper(explicit_project="other-project-456")

    def test_create_hmac_key_user_project(self):
        self._create_hmac_key_helper(user_project="billed-project", timeout=42)

    def test_list_hmac_keys_defaults_empty(self):
        PROJECT = "PROJECT"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        http = _make_requests_session([_make_json_response({})])
        client._http_internal = http

        metadatas = list(client.list_hmac_keys())

        self.assertEqual(len(metadatas), 0)

        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "projects",
                PROJECT,
                "hmacKeys",
            ]
        )
        http.request.assert_called_once_with(
            method="GET",
            url=URI,
            data=None,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_list_hmac_keys_explicit_non_empty(self):
        from six.moves.urllib.parse import parse_qsl
        from google.cloud.storage.hmac_key import HMACKeyMetadata

        PROJECT = "PROJECT"
        OTHER_PROJECT = "other-project-456"
        MAX_RESULTS = 3
        EMAIL = "storage-user-123@example.com"
        ACCESS_ID = "ACCESS-ID"
        USER_PROJECT = "billed-project"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        response = {
            "kind": "storage#hmacKeysMetadata",
            "items": [
                {
                    "kind": "storage#hmacKeyMetadata",
                    "accessId": ACCESS_ID,
                    "serviceAccountEmail": EMAIL,
                }
            ],
        }

        http = _make_requests_session([_make_json_response(response)])
        client._http_internal = http

        metadatas = list(
            client.list_hmac_keys(
                max_results=MAX_RESULTS,
                service_account_email=EMAIL,
                show_deleted_keys=True,
                project_id=OTHER_PROJECT,
                user_project=USER_PROJECT,
                timeout=42,
            )
        )

        self.assertEqual(len(metadatas), len(response["items"]))

        for metadata, resource in zip(metadatas, response["items"]):
            self.assertIsInstance(metadata, HMACKeyMetadata)
            self.assertIs(metadata._client, client)
            self.assertEqual(metadata._properties, resource)

        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "projects",
                OTHER_PROJECT,
                "hmacKeys",
            ]
        )
        EXPECTED_QPARAMS = {
            "maxResults": str(MAX_RESULTS),
            "serviceAccountEmail": EMAIL,
            "showDeletedKeys": "True",
            "userProject": USER_PROJECT,
        }
        http.request.assert_called_once_with(
            method="GET", url=mock.ANY, data=None, headers=mock.ANY, timeout=42
        )
        kwargs = http.request.mock_calls[0].kwargs
        uri = kwargs["url"]
        base, qparam_str = uri.split("?")
        qparams = dict(parse_qsl(qparam_str))
        self.assertEqual(base, URI)
        self.assertEqual(qparams, EXPECTED_QPARAMS)

    def test_get_hmac_key_metadata_wo_project(self):
        from google.cloud.storage.hmac_key import HMACKeyMetadata

        PROJECT = "PROJECT"
        EMAIL = "storage-user-123@example.com"
        ACCESS_ID = "ACCESS-ID"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        resource = {
            "kind": "storage#hmacKeyMetadata",
            "accessId": ACCESS_ID,
            "projectId": PROJECT,
            "serviceAccountEmail": EMAIL,
        }

        http = _make_requests_session([_make_json_response(resource)])
        client._http_internal = http

        metadata = client.get_hmac_key_metadata(ACCESS_ID, timeout=42)

        self.assertIsInstance(metadata, HMACKeyMetadata)
        self.assertIs(metadata._client, client)
        self.assertEqual(metadata.access_id, ACCESS_ID)
        self.assertEqual(metadata.project, PROJECT)

        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "projects",
                PROJECT,
                "hmacKeys",
                ACCESS_ID,
            ]
        )
        http.request.assert_called_once_with(
            method="GET", url=URI, data=None, headers=mock.ANY, timeout=42
        )

    def test_get_hmac_key_metadata_w_project(self):
        from six.moves.urllib.parse import urlencode
        from google.cloud.storage.hmac_key import HMACKeyMetadata

        PROJECT = "PROJECT"
        OTHER_PROJECT = "other-project-456"
        EMAIL = "storage-user-123@example.com"
        ACCESS_ID = "ACCESS-ID"
        USER_PROJECT = "billed-project"
        CREDENTIALS = _make_credentials()
        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)

        resource = {
            "kind": "storage#hmacKeyMetadata",
            "accessId": ACCESS_ID,
            "projectId": OTHER_PROJECT,
            "serviceAccountEmail": EMAIL,
        }

        http = _make_requests_session([_make_json_response(resource)])
        client._http_internal = http

        metadata = client.get_hmac_key_metadata(
            ACCESS_ID, project_id=OTHER_PROJECT, user_project=USER_PROJECT
        )

        self.assertIsInstance(metadata, HMACKeyMetadata)
        self.assertIs(metadata._client, client)
        self.assertEqual(metadata.access_id, ACCESS_ID)
        self.assertEqual(metadata.project, OTHER_PROJECT)

        URI = "/".join(
            [
                client._connection.API_BASE_URL,
                "storage",
                client._connection.API_VERSION,
                "projects",
                OTHER_PROJECT,
                "hmacKeys",
                ACCESS_ID,
            ]
        )

        qs_params = {"userProject": USER_PROJECT}
        FULL_URI = "{}?{}".format(URI, urlencode(qs_params))

        http.request.assert_called_once_with(
            method="GET",
            url=FULL_URI,
            data=None,
            headers=mock.ANY,
            timeout=self._get_default_timeout(),
        )

    def test_get_signed_policy_v4(self):
        import datetime

        BUCKET_NAME = "bucket-name"
        BLOB_NAME = "object-name"
        TIMESTAMP = "20200312T114716Z"

        credentials = _create_signing_credentials()
        credentials.sign_bytes = mock.Mock(return_value=b"Signature_bytes")
        credentials.signer_email = "test@mail.com"

        client = self._make_one(project="PROJECT")

        with mock.patch(
            "google.cloud.storage.client.get_v4_now_dtstamps",
            return_value=(TIMESTAMP, "20200312"),
        ):
            policy = client.get_signed_policy_v4(
                credentials,
                BUCKET_NAME,
                BLOB_NAME,
                conditions=[
                    {"bucket": BUCKET_NAME},
                    {"acl": "private"},
                    ["starts-with", "$Content-Type", "text/plain"],
                ],
                expiration=datetime.datetime(2020, 3, 12),
            )
        self.assertEqual(policy["url"], "https://storage.googleapis.com/" + BUCKET_NAME)
        self.assertEqual(policy["fields"]["key"], BLOB_NAME)
        self.assertEqual(policy["fields"]["x-goog-algorithm"], "GOOG4-RSA-SHA256")
        self.assertEqual(policy["fields"]["x-goog-date"], TIMESTAMP)
        self.assertEqual(
            policy["fields"]["x-goog-credential"],
            "test@mail.com/20200312/auto/storage/goog4_request",
        )
        self.assertEqual(
            policy["fields"]["x-goog-signature"], "5369676e61747572655f6279746573"
        )
        self.assertEqual(
            policy["fields"]["policy"],
            b"eyJjb25kaXRpb25zIjogW3siYnVja2V0IjogImJ1Y2tldC1uYW1lIn0sIHsiYWNsIjogInByaXZhdGUifSwgWyJzdGFydHMtd2l0aCIsICIkQ29udGVudC1UeXBlIiwgInRleHQvcGxhaW4iXV0sICJleHBpcmF0aW9uIjogIjIwMjAtMDMtMTJUMDA6MDA6MDAifQ==",
        )

    def test_get_signed_policy_v4_with_fields(self):
        import datetime

        BUCKET_NAME = "bucket-name"
        BLOB_NAME = "object-name"
        TIMESTAMP = "20200312T114716Z"
        FIELD1_VALUE = "Value1"

        credentials = _create_signing_credentials()
        credentials.sign_bytes = mock.Mock(return_value=b"Signature_bytes")
        credentials.signer_email = "test@mail.com"

        client = self._make_one(project="PROJECT")

        with mock.patch(
            "google.cloud.storage.client.get_v4_now_dtstamps",
            return_value=(TIMESTAMP, "20200312"),
        ):
            policy = client.get_signed_policy_v4(
                credentials,
                BUCKET_NAME,
                BLOB_NAME,
                conditions=[
                    {"bucket": BUCKET_NAME},
                    {"acl": "private"},
                    ["starts-with", "$Content-Type", "text/plain"],
                ],
                expiration=datetime.datetime(2020, 3, 12),
                fields={"field1": FIELD1_VALUE, "x-ignore-field": "Ignored_value"},
            )
        self.assertEqual(policy["url"], "https://storage.googleapis.com/" + BUCKET_NAME)
        self.assertEqual(policy["fields"]["key"], BLOB_NAME)
        self.assertEqual(policy["fields"]["x-goog-algorithm"], "GOOG4-RSA-SHA256")
        self.assertEqual(policy["fields"]["x-goog-date"], TIMESTAMP)
        self.assertEqual(policy["fields"]["field1"], FIELD1_VALUE)
        self.assertNotIn("x-ignore-field", policy["fields"].keys())
        self.assertEqual(
            policy["fields"]["x-goog-credential"],
            "test@mail.com/20200312/auto/storage/goog4_request",
        )
        self.assertEqual(
            policy["fields"]["x-goog-signature"], "5369676e61747572655f6279746573"
        )
        self.assertEqual(
            policy["fields"]["policy"],
            b"eyJjb25kaXRpb25zIjogW3siYnVja2V0IjogImJ1Y2tldC1uYW1lIn0sIHsiYWNsIjogInByaXZhdGUifSwgWyJzdGFydHMtd2l0aCIsICIkQ29udGVudC1UeXBlIiwgInRleHQvcGxhaW4iXV0sICJleHBpcmF0aW9uIjogIjIwMjAtMDMtMTJUMDA6MDA6MDAifQ==",
        )

    def test_get_signed_policy_v4_virtual_hosted_style(self):
        import datetime

        BUCKET_NAME = "bucket-name"
        BLOB_NAME = "object-name"
        TIMESTAMP = "20200312T114716Z"

        credentials = _create_signing_credentials()
        credentials.sign_bytes = mock.Mock(return_value=b"Signature_bytes")
        credentials.signer_email = "test@mail.com"

        client = self._make_one(project="PROJECT")

        with mock.patch(
            "google.cloud.storage.client.get_v4_now_dtstamps",
            return_value=(TIMESTAMP, "20200312"),
        ):
            policy = client.get_signed_policy_v4(
                credentials,
                BUCKET_NAME,
                BLOB_NAME,
                conditions=[],
                expiration=datetime.datetime(2020, 3, 12),
                virtual_hosted_style=True,
            )
        self.assertEqual(
            policy["url"], "https://{}.storage.googleapis.com".format(BUCKET_NAME)
        )

    def test_get_signed_policy_v4_bucket_bound_hostname(self):
        import datetime

        BUCKET_NAME = "bucket-name"
        BLOB_NAME = "object-name"
        TIMESTAMP = "20200312T114716Z"

        credentials = _create_signing_credentials()
        credentials.sign_bytes = mock.Mock(return_value=b"Signature_bytes")
        credentials.signer_email = "test@mail.com"

        client = self._make_one(project="PROJECT")

        with mock.patch(
            "google.cloud.storage.client.get_v4_now_dtstamps",
            return_value=(TIMESTAMP, "20200312"),
        ):
            policy = client.get_signed_policy_v4(
                credentials,
                BUCKET_NAME,
                BLOB_NAME,
                conditions=[],
                expiration=datetime.datetime(2020, 3, 12),
                bucket_bound_hostname="https://bucket.bound_hostname",
            )
        self.assertEqual(
            policy["url"], "https://bucket.bound_hostname/{}".format(BUCKET_NAME)
        )

    def test_get_signed_policy_v4_bucket_bound_hostname_with_scheme(self):
        import datetime

        BUCKET_NAME = "bucket-name"
        BLOB_NAME = "object-name"
        TIMESTAMP = "20200312T114716Z"

        credentials = _create_signing_credentials()
        credentials.sign_bytes = mock.Mock(return_value=b"Signature_bytes")
        credentials.signer_email = "test@mail.com"

        client = self._make_one(project="PROJECT")

        with mock.patch(
            "google.cloud.storage.client.get_v4_now_dtstamps",
            return_value=(TIMESTAMP, "20200312"),
        ):
            policy = client.get_signed_policy_v4(
                credentials,
                BUCKET_NAME,
                BLOB_NAME,
                conditions=[],
                expiration=datetime.datetime(2020, 3, 12),
                bucket_bound_hostname="bucket.bound_hostname",
                scheme="http",
            )
        self.assertEqual(
            policy["url"], "http://bucket.bound_hostname/{}".format(BUCKET_NAME)
        )

    def test_get_signed_policy_v4_no_expiration(self):
        import datetime

        BUCKET_NAME = "bucket-name"
        BLOB_NAME = "object-name"
        TIMESTAMP = "20200312T114716Z"

        credentials = _create_signing_credentials()
        credentials.sign_bytes = mock.Mock(return_value=b"Signature_bytes")
        credentials.signer_email = "test@mail.com"

        client = self._make_one(project="PROJECT")

        with mock.patch(
            "google.cloud.storage.client._NOW",
            return_value=datetime.datetime(2020, 3, 12),
        ) as now_mock:
            with mock.patch(
                "google.cloud.storage.client.get_v4_now_dtstamps",
                return_value=(TIMESTAMP, "20200312"),
            ):
                policy = client.get_signed_policy_v4(
                    credentials, BUCKET_NAME, BLOB_NAME, conditions=[], expiration=None
                )
                now_mock.assert_called_once()

        self.assertEqual(policy["url"], "https://storage.googleapis.com/" + BUCKET_NAME)
        self.assertEqual(
            policy["fields"]["policy"],
            b"eyJjb25kaXRpb25zIjogW10sICJleHBpcmF0aW9uIjogIjIwMjAtMDMtMTJUMDE6MDA6MDAifQ==",
        )

    def test_get_signed_policy_v4_with_access_token(self):
        import datetime

        BUCKET_NAME = "bucket-name"
        BLOB_NAME = "object-name"
        TIMESTAMP = "20200312T114716Z"

        client = self._make_one(project="PROJECT")

        credentials = _create_signing_credentials()
        credentials.signer_email = "test@mail.com"

        with mock.patch(
            "google.cloud.storage.client.get_v4_now_dtstamps",
            return_value=(TIMESTAMP, "20200312"),
        ):
            with mock.patch(
                "google.cloud.storage.client._sign_message", return_value=b"DEADBEEF"
            ):
                policy = client.get_signed_policy_v4(
                    credentials,
                    BUCKET_NAME,
                    BLOB_NAME,
                    conditions=[
                        {"bucket": BUCKET_NAME},
                        {"acl": "private"},
                        ["starts-with", "$Content-Type", "text/plain"],
                    ],
                    expiration=datetime.datetime(2020, 3, 12),
                    service_account_email="test@mail.com",
                    access_token="token",
                )
        self.assertEqual(policy["url"], "https://storage.googleapis.com/" + BUCKET_NAME)
        self.assertEqual(policy["fields"]["key"], BLOB_NAME)
        self.assertEqual(policy["fields"]["x-goog-algorithm"], "GOOG4-RSA-SHA256")
        self.assertEqual(policy["fields"]["x-goog-date"], TIMESTAMP)
        self.assertEqual(
            policy["fields"]["x-goog-credential"],
            "test@mail.com/20200312/auto/storage/goog4_request",
        )
        self.assertEqual(policy["fields"]["x-goog-signature"], "0c4003044105")
        self.assertEqual(
            policy["fields"]["policy"],
            b"eyJjb25kaXRpb25zIjogW3siYnVja2V0IjogImJ1Y2tldC1uYW1lIn0sIHsiYWNsIjogInByaXZhdGUifSwgWyJzdGFydHMtd2l0aCIsICIkQ29udGVudC1UeXBlIiwgInRleHQvcGxhaW4iXV0sICJleHBpcmF0aW9uIjogIjIwMjAtMDMtMTJUMDA6MDA6MDAifQ==",
        )
