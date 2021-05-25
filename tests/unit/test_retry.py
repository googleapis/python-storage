# Copyright 2020 Google LLC
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
import uuid

from google.cloud import storage
from google.cloud.storage import _helpers

from . import _read_local_json

import mock
import pytest
import requests

import http

# http.client.HTTPConnection.debuglevel=5


class Test_should_retry(unittest.TestCase):
    def _call_fut(self, exc):
        from google.cloud.storage import retry

        return retry._should_retry(exc)

    def test_w_retryable_transport_error(self):
        from google.cloud.storage import retry
        from google.auth.exceptions import TransportError as eTransportError
        from requests import ConnectionError as rConnectionError

        caught_exc = rConnectionError("Remote end closed connection unexpected")
        exc = eTransportError(caught_exc)
        self.assertTrue(retry._should_retry(exc))

    def test_w_wrapped_type(self):
        from google.cloud.storage import retry

        for exc_type in retry._RETRYABLE_TYPES:
            exc = exc_type("testing")
            self.assertTrue(self._call_fut(exc))

    def test_w_google_api_call_error_hit(self):
        from google.api_core import exceptions

        exc = exceptions.GoogleAPICallError("testing")
        exc.code = 408
        self.assertTrue(self._call_fut(exc))

    def test_w_google_api_call_error_miss(self):
        from google.api_core import exceptions

        exc = exceptions.GoogleAPICallError("testing")
        exc.code = 999
        self.assertFalse(self._call_fut(exc))

    def test_w_requests_connection_error(self):
        exc = ValueError("testing")
        self.assertFalse(self._call_fut(exc))


class TestConditionalRetryPolicy(unittest.TestCase):
    def _make_one(self, retry_policy, conditional_predicate, required_kwargs):
        from google.cloud.storage import retry

        return retry.ConditionalRetryPolicy(
            retry_policy, conditional_predicate, required_kwargs
        )

    def test_ctor(self):
        retry_policy = mock.Mock()
        conditional_predicate = mock.Mock()
        required_kwargs = ("kwarg",)

        policy = self._make_one(retry_policy, conditional_predicate, required_kwargs)

        self.assertIs(policy.retry_policy, retry_policy)
        self.assertIs(policy.conditional_predicate, conditional_predicate)
        self.assertEqual(policy.required_kwargs, required_kwargs)

    def test_get_retry_policy_if_conditions_met_single_kwarg_hit(self):
        retry_policy = mock.Mock()
        conditional_predicate = mock.Mock(return_value=True)
        required_kwargs = ("foo",)
        policy = self._make_one(retry_policy, conditional_predicate, required_kwargs)

        kwargs = {"foo": 1, "bar": 2, "baz": 3}
        result = policy.get_retry_policy_if_conditions_met(**kwargs)

        self.assertIs(result, retry_policy)

        conditional_predicate.assert_called_once_with(1)

    def test_get_retry_policy_if_conditions_met_multiple_kwargs_miss(self):
        retry_policy = mock.Mock()
        conditional_predicate = mock.Mock(return_value=False)
        required_kwargs = ("foo", "bar")
        policy = self._make_one(retry_policy, conditional_predicate, required_kwargs)

        kwargs = {"foo": 1, "bar": 2, "baz": 3}
        result = policy.get_retry_policy_if_conditions_met(**kwargs)

        self.assertIsNone(result)

        conditional_predicate.assert_called_once_with(1, 2)


class Test_is_generation_specified(unittest.TestCase):
    def _call_fut(self, query_params):
        from google.cloud.storage import retry

        return retry.is_generation_specified(query_params)

    def test_w_empty(self):
        query_params = {}

        self.assertFalse(self._call_fut(query_params))

    def test_w_generation(self):
        query_params = {"generation": 123}

        self.assertTrue(self._call_fut(query_params))

    def test_wo_generation_w_if_generation_match(self):
        query_params = {"ifGenerationMatch": 123}

        self.assertTrue(self._call_fut(query_params))


class Test_is_metageneration_specified(unittest.TestCase):
    def _call_fut(self, query_params):
        from google.cloud.storage import retry

        return retry.is_metageneration_specified(query_params)

    def test_w_empty(self):
        query_params = {}

        self.assertFalse(self._call_fut(query_params))

    def test_w_if_metageneration_match(self):
        query_params = {"ifMetagenerationMatch": 123}

        self.assertTrue(self._call_fut(query_params))


class Test_is_etag_in_json(unittest.TestCase):
    def _call_fut(self, data):
        from google.cloud.storage import retry

        return retry.is_etag_in_json(data)

    @staticmethod
    def _make_json_data(**kw):
        import json

        return json.dumps(kw)

    def test_w_empty(self):
        data = self._make_json_data()

        self.assertFalse(self._call_fut(data))

    def test_w_etag_in_data(self):
        data = self._make_json_data(etag="123")

        self.assertTrue(self._call_fut(data))

    def test_w_empty_data(self):
        data = ""

        self.assertFalse(self._call_fut(data))


class Test_default_conditional_retry_policies(unittest.TestCase):
    def test_is_generation_specified_match_generation_match(self):
        from google.cloud.storage import retry

        query_dict = {}
        _helpers._add_generation_match_parameters(query_dict, if_generation_match=1)

        conditional_policy = retry.DEFAULT_RETRY_IF_GENERATION_SPECIFIED
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params=query_dict
        )
        self.assertEqual(policy, retry.DEFAULT_RETRY)

    def test_is_generation_specified_match_generation(self):
        from google.cloud.storage import retry

        query_dict = {"generation": 1}

        conditional_policy = retry.DEFAULT_RETRY_IF_GENERATION_SPECIFIED
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params=query_dict
        )
        self.assertEqual(policy, retry.DEFAULT_RETRY)

    def test_is_generation_specified_mismatch(self):
        from google.cloud.storage import retry

        query_dict = {}
        _helpers._add_generation_match_parameters(query_dict, if_metageneration_match=1)

        conditional_policy = retry.DEFAULT_RETRY_IF_GENERATION_SPECIFIED
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params=query_dict
        )
        self.assertEqual(policy, None)

    def test_is_metageneration_specified_match(self):
        from google.cloud.storage import retry

        query_dict = {}
        _helpers._add_generation_match_parameters(query_dict, if_metageneration_match=1)

        conditional_policy = retry.DEFAULT_RETRY_IF_METAGENERATION_SPECIFIED
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params=query_dict
        )
        self.assertEqual(policy, retry.DEFAULT_RETRY)

    def test_is_metageneration_specified_mismatch(self):
        from google.cloud.storage import retry

        query_dict = {}
        _helpers._add_generation_match_parameters(query_dict, if_generation_match=1)

        conditional_policy = retry.DEFAULT_RETRY_IF_METAGENERATION_SPECIFIED
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params=query_dict
        )
        self.assertEqual(policy, None)

    def test_is_etag_in_json_etag_match(self):
        from google.cloud.storage import retry

        conditional_policy = retry.DEFAULT_RETRY_IF_ETAG_IN_JSON
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params={"ifGenerationMatch": 1}, data='{"etag": "12345678"}'
        )
        self.assertEqual(policy, retry.DEFAULT_RETRY)

    def test_is_etag_in_json_mismatch(self):
        from google.cloud.storage import retry

        conditional_policy = retry.DEFAULT_RETRY_IF_ETAG_IN_JSON
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params={"ifGenerationMatch": 1}, data="{}"
        )
        self.assertEqual(policy, None)

    def test_is_meta_or_etag_in_json_invalid(self):
        from google.cloud.storage import retry

        conditional_policy = retry.DEFAULT_RETRY_IF_ETAG_IN_JSON
        policy = conditional_policy.get_retry_policy_if_conditions_met(
            query_params={"ifGenerationMatch": 1}, data="I am invalid JSON!"
        )
        self.assertEqual(policy, None)


# ToDo: Confirm what are the credentials required. Can we use the same service account created for url_signer_v4_test_account?
_FAKE_SERVICE_ACCOUNT = None


def fake_service_account():
    global _FAKE_SERVICE_ACCOUNT
    # validate and set fake service account


# ToDo: Confirm what are the credentials required. Can we use the same service account created for url_signer_v4_test_account? )
# _SERVICE_ACCOUNT_JSON = _read_local_json("")
_CONFORMANCE_TESTS = _read_local_json("retry_strategy_test_data.json")[
    "retryStrategyTests"
]
# ToDo: Confirm the correct access endpoint.
_API_ACCESS_ENDPOINT = _helpers._get_storage_host()
_DEFAULT_STORAGE_HOST = u"https://storage.googleapis.com"
_CONF_TEST_PROJECT_ID = "my-project-id"
_CONF_TEST_SERVICE_ACCOUNT_EMAIL = (
    "my-service-account@my-project-id.iam.gserviceaccount.com"
)

########################################################################################################################################
### Library methods for mapping ########################################################################################################
########################################################################################################################################


def list_buckets(client, _, _bucket):
    buckets = client.list_buckets()
    for b in buckets:
        break


def list_blobs(client, _, bucket, _blob):
    blobs = client.list_blobs(bucket.name)
    for b in blobs:
        break


def get_blob(client, _, bucket, object):
    bucket = client.bucket(bucket.name)
    bucket.get_blob(object.name)


def reload_bucket(client, _, bucket):
    bucket = client.bucket(bucket.name)
    bucket.reload()


def get_bucket(client, _, bucket):
    client.get_bucket(bucket.name)


def update_blob(client, preconditions, bucket, object):
    bucket = client.bucket(bucket.name)
    blob = bucket.blob(object.name)
    metadata = {"foo": "bar"}
    blob.metadata = metadata
    if preconditions:
        metageneration = object.metageneration
        blob.patch(if_metageneration_match=metageneration)
    else:
        blob.patch()


def create_bucket(client, _):
    bucket = client.bucket(uuid.uuid4().hex)
    client.create_bucket(bucket)


# Q!!! upload_from_string did not retry.
def upload_from_string(client, _, bucket):
    bucket = client.get_bucket(bucket.name)
    blob = bucket.blob(uuid.uuid4().hex)
    blob.upload_from_string("upload from string")


def create_notification(client, _, bucket):
    bucket = client.get_bucket(bucket.name)
    notification = bucket.notification()
    notification.create()


def list_notifications(client, _, bucket, _notification):
    bucket = client.get_bucket(bucket.name)
    notifications = bucket.list_notifications()
    for n in notifications:
        break


def get_notification(client, _, bucket, notification):
    client.bucket(bucket.name).get_notification(notification.notification_id)


def delete_notification(client, _, bucket, notification):
    notification = client.bucket(bucket.name).get_notification(notification.notification_id)
    notification.delete()


# Q!!! are there hmacKeys retryable endpoints in the emulator?
def list_hmac_keys(client, _, _hmac_key):
    hmac_keys = client.list_hmac_keys()
    for k in hmac_keys:
        break


def delete_bucket(client, _, bucket):
    bucket = client.bucket(bucket.name)
    bucket.delete()


def get_iam_policy(client, _, bucket):
    bucket = client.bucket(bucket.name)
    bucket.get_iam_policy()


# Method invocation mapping. Methods to retry. This is a map whose keys are a string describing a standard
# API call (e.g. storage.objects.get) and values are a list of functions which
# wrap library methods that implement these calls. There may be multiple values
# because multiple library methods may use the same call (e.g. get could be a
# read or just a metadata get).
method_mapping = {
    "storage.bucket_acl.get": [],  # S1 start
    "storage.bucket_acl.list": [],
    "storage.buckets.delete": [delete_bucket],
    "storage.buckets.get": [get_bucket, reload_bucket],
    "storage.buckets.getIamPolicy": [get_iam_policy],
    "storage.buckets.insert": [create_bucket],
    "storage.buckets.list": [list_buckets],
    "storage.buckets.lockRententionPolicy": [],
    "storage.buckets.testIamPermission": [],
    "storage.default_object_acl.get": [],
    "storage.default_object_acl.list": [],
    "storage.hmacKey.delete": [],
    "storage.hmacKey.list": [],
    "storage.hmacKey.get": [],
    "storage.notifications.delete": [delete_notification],
    "storage.notifications.get": [get_notification],
    "storage.notifications.list": [list_notifications],
    "storage.object_acl.get": [],
    "storage.object_acl.list": [],
    "storage.objects.get": [get_blob],
    "storage.objects.list": [list_blobs],
    "storage.serviceaccount.get": [],  # S1 end
    "storage.buckets.patch": [],  # S2 start
    "storage.buckets.setIamPolicy": [],
    "storage.buckets.update": [],
    "storage.hmacKey.update": [],
    "storage.objects.compose": [],
    "storage.objects.copy": [],
    "storage.objects.delete": [],
    "storage.objects.insert": [],
    "storage.objects.patch": [update_blob],
    "storage.objects.rewrite": [],
    "storage.objects.update": [],  # S2 end
    "storage.notifications.insert": [create_notification],  # S4
}

########################################################################################################################################
### Helper Methods for Populating Resources ############################################################################################
########################################################################################################################################


def _populate_resource_bucket(client, resources):
    bucket = client.bucket(uuid.uuid4().hex)
    client.create_bucket(bucket)
    resources["bucket"] = bucket


def _populate_resource_object(client, resources):
    bucket_name = resources["bucket"].name
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(uuid.uuid4().hex)
    blob.upload_from_string("hello world")
    blob.reload()
    resources["object"] = blob


def _populate_resource_notification(client, resources):
    bucket_name = resources["bucket"].name
    bucket = client.get_bucket(bucket_name)
    notification = bucket.notification()
    notification.create()
    notification.reload()
    resources["notification"] = notification


def _populate_resource_hmackey(client, resources):
    hmac_key, secret = client.create_hmac_key(
        service_account_email=_CONF_TEST_SERVICE_ACCOUNT_EMAIL,
        project_id=_CONF_TEST_PROJECT_ID,
    )
    resources["hmac_key"] = hmac_key


resource_mapping = {
    "BUCKET": _populate_resource_bucket,
    "OBJECT": _populate_resource_object,
    "NOTIFICATION": _populate_resource_notification,
    "HMAC_KEY": _populate_resource_hmackey,
}


def _populate_resources(client, json_resource):
    resources = {}

    for r in json_resource:
        try:
            func = resource_mapping[r]
            func(client, resources)
        except Exception as e:
            print("log warning here: {}".format(e))

    return resources


########################################################################################################################################
### Helper Methods for Emulator Retry API ##############################################################################################
########################################################################################################################################


def _create_retry_test(host, method_name, instructions):
    import json

    preflight_post_uri = host + "/retry_test"
    headers = {
        "Content-Type": "application/json",
    }
    data_dict = {"instructions": {method_name: instructions}}
    data = json.dumps(data_dict)
    try:
        r = requests.post(preflight_post_uri, headers=headers, data=data)
        return r.json()
    except Exception as e:
        print(e.args)
        # do something
        return None


def _check_retry_test(host, id):
    status_get_uri = "{base}{retry}/{id}".format(base=host, retry="/retry_test", id=id)
    try:
        r = requests.get(status_get_uri)
        return r.json()
    except Exception as e:
        print(e.args)
        # do something
        return None


def _run_retry_test(host, id, func, preconditions, **resources):
    # Create client using x-retry-test-id header.
    client = storage.Client(client_options={"api_endpoint": host})
    client._http.headers.update({"x-retry-test-id": id})
    func(client, preconditions, **resources)


def _delete_retry_test(host, id):
    status_get_uri = "{base}{retry}/{id}".format(base=host, retry="/retry_test", id=id)
    try:
        requests.delete(status_get_uri)
    except Exception as e:
        print(e.args)
        # do something


########################################################################################################################################
### Run Conformance Tests for Retry Strategy ###########################################################################################
########################################################################################################################################


@pytest.mark.parametrize("test_data", _CONFORMANCE_TESTS)
def test_conformance_retry_strategy(test_data):
    host = _API_ACCESS_ENDPOINT
    if host == _DEFAULT_STORAGE_HOST:
        pytest.skip(
            "This test must use the testbench emulator; set STORAGE_EMULATOR_HOST to run."
        )

    # Create client to use for setup steps.
    client = storage.Client()
    methods = test_data["methods"]
    cases = test_data["cases"]
    expect_success = test_data["expectSuccess"]
    precondition_provided = test_data["preconditionProvided"]
    for c in cases:
        for m in methods:
            # Extract method name and instructions to create retry test.
            method_name = m["name"]
            instructions = c["instructions"]
            json_resources = m["resources"]

            if method_name not in method_mapping:
                # TODO(cathyo@): change to log warning
                print("No tests for operation {}".format(method_name))
                continue

            for function in method_mapping[method_name]:
                # Create the retry test in the emulator to handle instructions.
                r = _create_retry_test(host, method_name, instructions)
                if r:
                    id = r["id"]
                else:
                    # TODO(cathyo@): change to log warning
                    print("Error creating retry test")
                    continue

                # Populate resources.
                resources = _populate_resources(client, json_resources)

                # Run retry tests on library methods.
                try:
                    _run_retry_test(
                        host,
                        id,
                        function,
                        precondition_provided,
                        **resources
                    )
                except Exception as e:
                    print(e)
                    success_results = False
                else:
                    success_results = True

                # Assert expected success for each scenario.
                assert expect_success == success_results

                # Verify that all instructions were used up during the test
                # (indicates that the client sent the correct requests).
                status_response = _check_retry_test(host, id)
                if status_response:
                    test_complete = status_response["completed"]
                    assert test_complete == True
                else:
                    print("do something")

                # Clean up and close out test in emulator.
                _delete_retry_test(host, id)
