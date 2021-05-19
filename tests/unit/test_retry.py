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

from google.cloud import storage
from google.cloud.storage import _helpers

from . import _read_local_json

import mock
import pytest
import requests

import http
http.client.HTTPConnection.debuglevel=5

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
_CONFORMANCE_TESTS = _read_local_json("retry_strategy_test_data.json")["retryStrategyTests"]
# ToDo: Confirm the correct access endpoint.
_API_ACCESS_ENDPOINT = _helpers._get_storage_host()
_DEFAULT_STORAGE_HOST = u"https://storage.googleapis.com"

# Library methods for mapping
def list_buckets():
    from google.cloud import storage
    client = storage.Client()
    bucket = client.list_buckets()

def get_blob(client, resource):
    from google.cloud import storage
    client = storage.Client()
    bucket = client.bucket(resource["bucket"]["name"])
    bucket.get_blob(resource["object"]["name"])

def download_blob_to_file(client, resource):
    client.download_blob_to_file(resource["object"]["name"], resource["file_handle"]) #file handle in resource?

def reload_bucket(client, resource):
    bucket = Bucket(client, resource["bucket"]["name"])
    bucket.reload()

def get_bucket(client, resource):
    bucket_name = "bucket"      #resource["bucket"]["name"]
    client.get_bucket(bucket_name)

# Method invocation mapping. Methods to retry. This is a map whose keys are a string describing a standard
# API call (e.g. storage.objects.get) and values are a list of functions which
# wrap library methods that implement these calls. There may be multiple values
# because multiple library methods may use the same call (e.g. get could be a
# read or just a metadata get).
method_mapping = {
    "storage.buckets.list": [
        get_bucket,
        get_bucket 
    ],
    "storage.objects.get": [
        get_bucket,
        get_bucket 
    ],
    "storage.buckets.get": [
        get_bucket
    ],
    "storage.notification.create": [
        get_bucket
    ]
}


def _create_retry_test(method_name, instructions):
    import json

    preflight_post_uri = _API_ACCESS_ENDPOINT + "/retry_test"
    headers = {
        'Content-Type': 'application/json',
    }
    data_dict = {
        'instructions': {
            method_name: instructions
        }
    }
    data = json.dumps(data_dict)
    try:
        r = requests.post(preflight_post_uri, headers=headers, data=data)
        return r.json()
    except Exception as e:
        print(e.args)
        # do something
        return None


def _check_retry_test(id):
    status_get_uri = "{base}{retry}/{id}".format(base=_API_ACCESS_ENDPOINT, retry="/retry_test", id=id)
    try:
        r = requests.get(status_get_uri)
        return r.json()
    except Exception as e:
        print(e.args)
        # do something
        return None

def _run_retry_test(id, func, resource=None):
    test_run_uri = _API_ACCESS_ENDPOINT + "/storage/v1/b?project=test"
    client = storage.Client(client_options={"api_endpoint": test_run_uri})
    client._http.headers.update({"x-retry-test-id": id})
    func(client=client, resource=resource)


def _delete_retry_test(id):
    status_get_uri = "{base}{retry}/{id}".format(base=_API_ACCESS_ENDPOINT, retry="/retry_test", id=id)
    try:
        r = requests.delete(status_get_uri)
    except Exception as e:
        print(e.args)
        # do something


@pytest.mark.parametrize("test_data", _CONFORMANCE_TESTS)
def test_conformance_retry_strategy(test_data):
    if _API_ACCESS_ENDPOINT == _DEFAULT_STORAGE_HOST:
        pytest.skip("This test must use the testbench emulator; set STORAGE_EMULATOR_HOST to run.")

    methods = test_data["methods"]
    cases = test_data["cases"]
    expect_success = test_data["expectSuccess"]
    for c in cases:
        for m in methods:
            # Extract method name and instructions to create retry test.
            method_name = m["name"]
            instructions = c["instructions"]

            if method_name not in method_mapping:
                # TODO(cathyo@): change to log warning
                print("No tests for operation {}".format(method_name))
                continue

            for function in method_mapping[method_name]:
                # Create the retry test in the emulator to handle instructions.
                r = _create_retry_test(method_name, instructions)
                if r:
                    id = r["id"]
                else:
                    # TODO(cathyo@): change to log warning
                    print("Error creating retry test")
                    continue

                # Run retry tests on library methods
                _run_retry_test(id, func=function)

                # Verify that all instructions were used up during the test
				# (indicates that the client sent the correct requests).
                status_response = _check_retry_test(id)
                if status_response:
                    test_complete = status_response["completed"]
                    # assert test_complete == True
                else:
                    print("do something")

                # Clean up and close out test in emulator.
                _delete_retry_test(id)
