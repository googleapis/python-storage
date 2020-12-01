# Copyright 2019 Google LLC
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

import mock

from google.cloud.storage.retry import DEFAULT_RETRY
from google.cloud.storage.retry import DEFAULT_RETRY_IF_ETAG_IN_JSON


class TestHMACKeyMetadata(unittest.TestCase):
    @staticmethod
    def _get_default_timeout():
        from google.cloud.storage.constants import _DEFAULT_TIMEOUT

        return _DEFAULT_TIMEOUT

    @staticmethod
    def _get_target_class():
        from google.cloud.storage.hmac_key import HMACKeyMetadata

        return HMACKeyMetadata

    def _make_one(self, client=None, *args, **kw):
        if client is None:
            client = _Client()
        return self._get_target_class()(client, *args, **kw)

    def test_ctor_defaults(self):
        client = object()
        metadata = self._make_one(client)
        self.assertIs(metadata._client, client)
        self.assertEqual(metadata._properties, {})
        self.assertIsNone(metadata.access_id)
        self.assertIsNone(metadata.etag)
        self.assertIsNone(metadata.id)
        self.assertIsNone(metadata.project)
        self.assertIsNone(metadata.service_account_email)
        self.assertIsNone(metadata.state)
        self.assertIsNone(metadata.time_created)
        self.assertIsNone(metadata.updated)

    def test_ctor_explicit(self):
        OTHER_PROJECT = "other-project-456"
        ACCESS_ID = "access-id-123456789"
        USER_PROJECT = "billed-project"
        client = _Client()
        metadata = self._make_one(
            client,
            access_id=ACCESS_ID,
            project_id=OTHER_PROJECT,
            user_project=USER_PROJECT,
        )
        self.assertIs(metadata._client, client)
        expected = {"accessId": ACCESS_ID, "projectId": OTHER_PROJECT}
        self.assertEqual(metadata._properties, expected)
        self.assertEqual(metadata.access_id, ACCESS_ID)
        self.assertEqual(metadata.user_project, USER_PROJECT)
        self.assertIsNone(metadata.etag)
        self.assertIsNone(metadata.id)
        self.assertEqual(metadata.project, OTHER_PROJECT)
        self.assertIsNone(metadata.service_account_email)
        self.assertIsNone(metadata.state)
        self.assertIsNone(metadata.time_created)
        self.assertIsNone(metadata.updated)

    def test___eq___other_type(self):
        metadata = self._make_one()
        for bogus in (None, "bogus", 123, 456.78, [], (), {}, set()):
            self.assertNotEqual(metadata, bogus)

    def test___eq___mismatched_client(self):
        metadata = self._make_one()
        other_client = _Client(project="other-project-456")
        other = self._make_one(other_client)
        self.assertNotEqual(metadata, other)

    def test___eq___mismatched_access_id(self):
        metadata = self._make_one()
        metadata._properties["accessId"] = "ABC123"
        other = self._make_one(metadata._client)
        metadata._properties["accessId"] = "DEF456"
        self.assertNotEqual(metadata, other)

    def test___eq___hit(self):
        metadata = self._make_one()
        metadata._properties["accessId"] = "ABC123"
        other = self._make_one(metadata._client)
        other._properties["accessId"] = metadata.access_id
        self.assertEqual(metadata, other)

    def test___hash__(self):
        client = _Client()
        metadata = self._make_one(client)
        metadata._properties["accessId"] = "ABC123"
        self.assertIsInstance(hash(metadata), int)
        other = self._make_one(client)
        metadata._properties["accessId"] = "DEF456"
        self.assertNotEqual(hash(metadata), hash(other))

    def test_access_id_getter(self):
        metadata = self._make_one()
        expected = "ACCESS-ID"
        metadata._properties["accessId"] = expected
        self.assertEqual(metadata.access_id, expected)

    def test_etag_getter(self):
        metadata = self._make_one()
        expected = "ETAG"
        metadata._properties["etag"] = expected
        self.assertEqual(metadata.etag, expected)

    def test_id_getter(self):
        metadata = self._make_one()
        expected = "ID"
        metadata._properties["id"] = expected
        self.assertEqual(metadata.id, expected)

    def test_project_getter(self):
        metadata = self._make_one()
        expected = "PROJECT-ID"
        metadata._properties["projectId"] = expected
        self.assertEqual(metadata.project, expected)

    def test_service_account_email_getter(self):
        metadata = self._make_one()
        expected = "service_account@example.com"
        metadata._properties["serviceAccountEmail"] = expected
        self.assertEqual(metadata.service_account_email, expected)

    def test_state_getter(self):
        metadata = self._make_one()
        expected = "STATE"
        metadata._properties["state"] = expected
        self.assertEqual(metadata.state, expected)

    def test_state_setter_invalid_state(self):
        metadata = self._make_one()
        expected = "INVALID"

        with self.assertRaises(ValueError):
            metadata.state = expected

        self.assertIsNone(metadata.state)

    def test_state_setter_inactive(self):
        metadata = self._make_one()
        metadata._properties["state"] = "ACTIVE"
        expected = "INACTIVE"
        metadata.state = expected
        self.assertEqual(metadata.state, expected)
        self.assertEqual(metadata._properties["state"], expected)

    def test_state_setter_active(self):
        metadata = self._make_one()
        metadata._properties["state"] = "INACTIVE"
        expected = "ACTIVE"
        metadata.state = expected
        self.assertEqual(metadata.state, expected)
        self.assertEqual(metadata._properties["state"], expected)

    def test_time_created_getter(self):
        import datetime
        from pytz import UTC

        metadata = self._make_one()
        now = datetime.datetime.utcnow()
        now_stamp = "{}Z".format(now.isoformat())
        metadata._properties["timeCreated"] = now_stamp
        self.assertEqual(metadata.time_created, now.replace(tzinfo=UTC))

    def test_updated_getter(self):
        import datetime
        from pytz import UTC

        metadata = self._make_one()
        now = datetime.datetime.utcnow()
        now_stamp = "{}Z".format(now.isoformat())
        metadata._properties["updated"] = now_stamp
        self.assertEqual(metadata.updated, now.replace(tzinfo=UTC))

    def test_path_wo_access_id(self):
        metadata = self._make_one()

        with self.assertRaises(ValueError):
            metadata.path

    def test_path_w_access_id_wo_project(self):
        access_id = "ACCESS-ID"
        client = _Client()
        metadata = self._make_one()
        metadata._properties["accessId"] = access_id

        expected_path = "/projects/{}/hmacKeys/{}".format(
            client.DEFAULT_PROJECT, access_id
        )
        self.assertEqual(metadata.path, expected_path)

    def test_path_w_access_id_w_explicit_project(self):
        access_id = "ACCESS-ID"
        project = "OTHER-PROJECT"
        metadata = self._make_one()
        metadata._properties["accessId"] = access_id
        metadata._properties["projectId"] = project

        expected_path = "/projects/{}/hmacKeys/{}".format(project, access_id)
        self.assertEqual(metadata.path, expected_path)

    def test_exists_miss_no_project_set(self):
        from google.cloud.exceptions import NotFound

        access_id = "ACCESS-ID"
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.side_effect = NotFound("testing")
        client = _Client(connection)
        metadata = self._make_one(client)
        metadata._properties["accessId"] = access_id

        self.assertFalse(metadata.exists(timeout=42))

        expected_path = "/projects/{}/hmacKeys/{}".format(
            client.DEFAULT_PROJECT, access_id
        )
        expected_kwargs = {
            "method": "GET",
            "path": expected_path,
            "query_params": {},
            "timeout": 42,
            "retry": DEFAULT_RETRY,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)

    def test_exists_hit_w_project_set(self):
        project = "PROJECT-ID"
        access_id = "ACCESS-ID"
        user_project = "billed-project"
        email = "service-account@example.com"
        resource = {
            "kind": "storage#hmacKeyMetadata",
            "accessId": access_id,
            "serviceAccountEmail": email,
        }
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.return_value = resource
        client = _Client(connection)
        metadata = self._make_one(client, user_project=user_project)
        metadata._properties["accessId"] = access_id
        metadata._properties["projectId"] = project

        self.assertTrue(metadata.exists())

        expected_path = "/projects/{}/hmacKeys/{}".format(project, access_id)
        expected_kwargs = {
            "method": "GET",
            "path": expected_path,
            "query_params": {"userProject": user_project},
            "timeout": self._get_default_timeout(),
            "retry": DEFAULT_RETRY,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)

    def test_reload_miss_no_project_set(self):
        from google.cloud.exceptions import NotFound

        access_id = "ACCESS-ID"
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.side_effect = NotFound("testing")
        client = _Client(connection)
        metadata = self._make_one(client)
        metadata._properties["accessId"] = access_id

        with self.assertRaises(NotFound):
            metadata.reload(timeout=42)

        expected_path = "/projects/{}/hmacKeys/{}".format(
            client.DEFAULT_PROJECT, access_id
        )
        expected_kwargs = {
            "method": "GET",
            "path": expected_path,
            "query_params": {},
            "timeout": 42,
            "retry": DEFAULT_RETRY,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)

    def test_reload_hit_w_project_set(self):
        project = "PROJECT-ID"
        access_id = "ACCESS-ID"
        user_project = "billed-project"
        email = "service-account@example.com"
        resource = {
            "kind": "storage#hmacKeyMetadata",
            "accessId": access_id,
            "serviceAccountEmail": email,
        }
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.return_value = resource
        client = _Client(connection)
        metadata = self._make_one(client, user_project=user_project)
        metadata._properties["accessId"] = access_id
        metadata._properties["projectId"] = project

        metadata.reload()

        self.assertEqual(metadata._properties, resource)

        expected_path = "/projects/{}/hmacKeys/{}".format(project, access_id)
        expected_kwargs = {
            "method": "GET",
            "path": expected_path,
            "query_params": {"userProject": user_project},
            "timeout": self._get_default_timeout(),
            "retry": DEFAULT_RETRY,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)

    def test_update_miss_no_project_set(self):
        from google.cloud.exceptions import NotFound

        access_id = "ACCESS-ID"
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.side_effect = NotFound("testing")
        client = _Client(connection)
        metadata = self._make_one(client)
        metadata._properties["accessId"] = access_id
        metadata.state = "INACTIVE"

        with self.assertRaises(NotFound):
            metadata.update(timeout=42)

        expected_path = "/projects/{}/hmacKeys/{}".format(
            client.DEFAULT_PROJECT, access_id
        )
        expected_kwargs = {
            "method": "PUT",
            "path": expected_path,
            "data": {"state": "INACTIVE"},
            "query_params": {},
            "timeout": 42,
            "retry": DEFAULT_RETRY_IF_ETAG_IN_JSON,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)

    def test_update_hit_w_project_set(self):
        project = "PROJECT-ID"
        access_id = "ACCESS-ID"
        user_project = "billed-project"
        email = "service-account@example.com"
        resource = {
            "kind": "storage#hmacKeyMetadata",
            "accessId": access_id,
            "serviceAccountEmail": email,
            "state": "ACTIVE",
        }
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.return_value = resource
        client = _Client(connection)
        metadata = self._make_one(client, user_project=user_project)
        metadata._properties["accessId"] = access_id
        metadata._properties["projectId"] = project
        metadata.state = "ACTIVE"

        metadata.update()

        self.assertEqual(metadata._properties, resource)

        expected_path = "/projects/{}/hmacKeys/{}".format(project, access_id)
        expected_kwargs = {
            "method": "PUT",
            "path": expected_path,
            "data": {"state": "ACTIVE"},
            "query_params": {"userProject": user_project},
            "timeout": self._get_default_timeout(),
            "retry": DEFAULT_RETRY_IF_ETAG_IN_JSON,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)

    def test_delete_not_inactive(self):
        metadata = self._make_one()
        for state in ("ACTIVE", "DELETED"):
            metadata._properties["state"] = state

            with self.assertRaises(ValueError):
                metadata.delete()

    def test_delete_miss_no_project_set(self):
        from google.cloud.exceptions import NotFound

        access_id = "ACCESS-ID"
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.side_effect = NotFound("testing")
        client = _Client(connection)
        metadata = self._make_one(client)
        metadata._properties["accessId"] = access_id
        metadata.state = "INACTIVE"

        with self.assertRaises(NotFound):
            metadata.delete(timeout=42)

        expected_path = "/projects/{}/hmacKeys/{}".format(
            client.DEFAULT_PROJECT, access_id
        )
        expected_kwargs = {
            "method": "DELETE",
            "path": expected_path,
            "query_params": {},
            "timeout": 42,
            "retry": DEFAULT_RETRY,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)

    def test_delete_hit_w_project_set(self):
        project = "PROJECT-ID"
        access_id = "ACCESS-ID"
        user_project = "billed-project"
        connection = mock.Mock(spec=["api_request"])
        connection.api_request.return_value = {}
        client = _Client(connection)
        metadata = self._make_one(client, user_project=user_project)
        metadata._properties["accessId"] = access_id
        metadata._properties["projectId"] = project
        metadata.state = "INACTIVE"

        metadata.delete()

        expected_path = "/projects/{}/hmacKeys/{}".format(project, access_id)
        expected_kwargs = {
            "method": "DELETE",
            "path": expected_path,
            "query_params": {"userProject": user_project},
            "timeout": self._get_default_timeout(),
            "retry": DEFAULT_RETRY,
        }
        connection.api_request.assert_called_once_with(**expected_kwargs)


class _Client(object):
    DEFAULT_PROJECT = "project-123"

    def __init__(self, connection=None, project=DEFAULT_PROJECT):
        self._connection = connection
        self.project = project

    def __eq__(self, other):
        if not isinstance(other, self.__class__):  # pragma: NO COVER
            return NotImplemented
        return self._connection == other._connection and self.project == other.project

    def __hash__(self):
        return hash(self._connection) + hash(self.project)
