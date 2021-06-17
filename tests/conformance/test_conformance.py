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

import uuid

from google.cloud import storage

from . import _read_local_json

import os
import pytest
import requests
import warnings


_CONFORMANCE_TESTS = _read_local_json("retry_strategy_test_data.json")[
    "retryStrategyTests"
]

STORAGE_EMULATOR_ENV_VAR = "STORAGE_EMULATOR_HOST"
"""Environment variable defining host for Storage emulator."""

_CONF_TEST_PROJECT_ID = "my-project-id"
_CONF_TEST_SERVICE_ACCOUNT_EMAIL = (
    "my-service-account@my-project-id.iam.gserviceaccount.com"
)

########################################################################################################################################
### Library methods for mapping ########################################################################################################
########################################################################################################################################


def list_buckets(client, _preconditions, **_):
    buckets = client.list_buckets()
    for b in buckets:
        print(b)


def list_blobs(client, _preconditions, bucket, **_):
    blobs = client.list_blobs(bucket.name)
    for b in blobs:
        print(b)


def get_blob(client, _preconditions, bucket, object):
    bucket = client.bucket(bucket.name)
    bucket.get_blob(object.name)


def reload_bucket(client, _preconditions, bucket):
    bucket = client.bucket(bucket.name)
    bucket.reload()


def get_bucket(client, _preconditions, bucket):
    client.get_bucket(bucket.name)


def create_bucket(client, _preconditions):
    bucket = client.bucket(uuid.uuid4().hex)
    client.create_bucket(bucket)


def upload_from_string(client, _preconditions, bucket):
    blob = client.bucket(bucket.name).blob(uuid.uuid4().hex)
    if _preconditions:
        blob.upload_from_string("upload from string", if_metageneration_match=0)
    else:
        blob.upload_from_string("upload from string")


def create_notification(client, _preconditions, bucket):
    bucket = client.get_bucket(bucket.name)
    notification = bucket.notification()
    notification.create()


def list_notifications(client, _preconditions, bucket, **_):
    bucket = client.get_bucket(bucket.name)
    notifications = bucket.list_notifications()
    for n in notifications:
        print(n)


def get_notification(client, _preconditions, bucket, notification):
    client.bucket(bucket.name).get_notification(notification.notification_id)


def delete_notification(client, _preconditions, bucket, notification):
    notification = client.bucket(bucket.name).get_notification(
        notification.notification_id
    )
    notification.delete()


def list_hmac_keys(client, _preconditions, **_):
    hmac_keys = client.list_hmac_keys()
    for k in hmac_keys:
        print(k)


def delete_bucket(client, _preconditions, bucket):
    bucket = client.bucket(bucket.name)
    bucket.delete()


def get_iam_policy(client, _preconditions, bucket):
    bucket = client.bucket(bucket.name)
    bucket.get_iam_policy()


def get_iam_permissions(client, _preconditions, bucket):
    bucket = client.bucket(bucket.name)
    permissions = ["storage.buckets.get", "storage.buckets.create"]
    bucket.test_iam_permissions(permissions)


def get_service_account_email(client, _preconditions):
    client.get_service_account_email()


def make_bucket_public(client, _preconditions, bucket):
    bucket = client.bucket(bucket.name)
    bucket.make_public()


def delete_blob(client, _preconditions, bucket, object):
    bucket = client.bucket(bucket.name)
    if _preconditions:
        generation = object.generation
        bucket.delete_blob(object.name, if_generation_match=generation)
    else:
        bucket.delete_blob(object.name)


def lock_retention_policy(client, _preconditions, bucket):
    bucket2 = client.bucket(bucket.name)
    bucket2.retention_period = 60
    bucket2.patch()
    bucket2.lock_retention_policy()


def patch_bucket(client, _preconditions, bucket):
    bucket = client.get_bucket("bucket")
    metageneration = bucket.metageneration
    bucket.storage_class = "COLDLINE"
    if _preconditions:
        bucket.patch(if_metageneration_match=metageneration)
    else:
        bucket.patch()


def update_bucket(client, _preconditions, bucket):
    bucket = client.get_bucket("bucket")
    metageneration = bucket.metageneration
    bucket._properties = {"storageClass": "STANDARD"}
    if _preconditions:
        bucket.update(if_metageneration_match=metageneration)
    else:
        bucket.update()


def patch_blob(client, _preconditions, bucket, object):
    blob = client.bucket(bucket.name).blob(object.name)
    blob.metadata = {"foo": "bar"}
    if _preconditions:
        blob.patch(if_metageneration_match=object.metageneration)
    else:
        blob.patch()


def update_blob(client, _preconditions, bucket, object):
    blob = client.bucket(bucket.name).blob(object.name)
    blob.metadata = {"foo": "bar"}
    if _preconditions:
        blob.update(if_metageneration_match=object.metageneration)
    else:
        blob.update()


def copy_blob(client, _preconditions, bucket, object):
    bucket = client.bucket(bucket.name)
    destination = client.bucket("bucket")
    if _preconditions:
        bucket.copy_blob(
            object, destination, new_name=uuid.uuid4().hex, if_generation_match=0
        )
    else:
        bucket.copy_blob(object, destination)


def rename_blob(client, _preconditions, bucket, object):
    bucket = client.bucket(bucket.name)
    new_name = uuid.uuid4().hex
    if _preconditions:
        bucket.rename_blob(object, new_name, if_generation_match=0)
    else:
        bucket.rename_blob(object, new_name)


def rewrite_blob(client, _preconditions, bucket, object):
    new_blob = client.bucket(bucket.name).blob(uuid.uuid4().hex)
    new_blob.metadata = {"foo": "bar"}
    if _preconditions:
        new_blob.rewrite(object, if_generation_match=0)
    else:
        new_blob.rewrite(object)


def compose_blob(client, _preconditions, bucket, object):
    blob = client.bucket(bucket.name).blob(object.name)
    blob_2 = bucket.blob(uuid.uuid4().hex)
    blob_2.upload_from_string("foo")
    sources = [blob_2]

    if _preconditions:
        blob.compose(sources, if_generation_match=object.generation)
    else:
        blob.compose(sources)


# Method invocation mapping. Methods to retry. This is a map whose keys are a string describing a standard
# API call (e.g. storage.objects.get) and values are a list of functions which
# wrap library methods that implement these calls. There may be multiple values
# because multiple library methods may use the same call (e.g. get could be a
# read or just a metadata get).
method_mapping = {
    "storage.buckets.delete": [delete_bucket],  # S1 start
    "storage.buckets.get": [get_bucket, reload_bucket],
    "storage.buckets.getIamPolicy": [get_iam_policy],
    "storage.buckets.insert": [create_bucket],
    "storage.buckets.list": [list_buckets],
    "storage.buckets.lockRententionPolicy": [],  # lock_retention_policy
    "storage.buckets.testIamPermission": [get_iam_permissions],
    "storage.notifications.delete": [delete_notification],
    "storage.notifications.get": [get_notification],
    "storage.notifications.list": [list_notifications],
    "storage.objects.get": [get_blob],
    "storage.objects.list": [list_blobs],  # S1 end
    "storage.buckets.patch": [patch_bucket],  # S2 start
    "storage.buckets.setIamPolicy": [],
    "storage.buckets.update": [update_bucket],
    "storage.objects.compose": [],  # compose_blob
    "storage.objects.copy": [copy_blob, rename_blob],
    "storage.objects.delete": [delete_blob],
    "storage.objects.insert": [upload_from_string],
    "storage.objects.patch": [patch_blob],
    "storage.objects.rewrite": [rewrite_blob],
    "storage.objects.update": [update_blob],  # S2 end
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
        func = resource_mapping[r]
        func(client, resources)

    return resources


########################################################################################################################################
### Helper Methods for Emulator Retry API ##############################################################################################
########################################################################################################################################


def _create_retry_test(host, method_name, instructions):
    """
    Initialize a Retry Test resource with a list of instructions and an API method.
    This offers a mechanism to send multiple retry instructions while sending a single, constant header through all the HTTP requests in a test.
    See also: https://github.com/googleapis/google-cloud-cpp/tree/main/google/cloud/storage/emulator
    """
    import json

    preflight_post_uri = host + "/retry_test"
    headers = {
        "Content-Type": "application/json",
    }
    data_dict = {"instructions": {method_name: instructions}}
    data = json.dumps(data_dict)
    r = requests.post(preflight_post_uri, headers=headers, data=data)
    return r.json()


def _get_retry_test(host, id):
    status_get_uri = "{base}{retry}/{id}".format(base=host, retry="/retry_test", id=id)
    r = requests.get(status_get_uri)
    return r.json()


def _run_retry_test(host, id, func, _preconditions, **resources):
    """
    To execute tests against the list of instrucions sent to the Retry API, create a client to send the retry test ID using the x-retry-test-id header in each request.
    For incoming requests which match the given API method, the emulator will pop off the next instruction from the list and force the listed failure case.
    """
    client = storage.Client(client_options={"api_endpoint": host})
    client._http.headers.update({"x-retry-test-id": id})
    func(client, _preconditions, **resources)


def _delete_retry_test(host, id):
    status_get_uri = "{base}{retry}/{id}".format(base=host, retry="/retry_test", id=id)
    requests.delete(status_get_uri)


########################################################################################################################################
### Run Conformance Tests for Retry Strategy ###########################################################################################
########################################################################################################################################


def pytest_generate_tests(metafunc):
    for test_data in _CONFORMANCE_TESTS:
        scenario_id = test_data["id"]
        m = "s{}method".format(scenario_id)
        c = "s{}case".format(scenario_id)
        s = "s{}".format(scenario_id)
        if s in metafunc.fixturenames:
            metafunc.parametrize(s, [scenario_id])
        if m in metafunc.fixturenames:
            metafunc.parametrize(m, test_data["methods"])
        if c in metafunc.fixturenames:
            metafunc.parametrize(c, test_data["cases"])


def test_retry_s1_always_idempotent(s1, s1method, s1case):
    run_retry_stragegy_conformance_test(s1, s1method, s1case)


def test_retry_s2_conditionally_idempotent_w_preconditions(s2, s2method, s2case):
    run_retry_stragegy_conformance_test(s2, s2method, s2case)


def run_retry_stragegy_conformance_test(scenario_id, method, case):
    host = os.environ.get(STORAGE_EMULATOR_ENV_VAR)
    if host is None:
        pytest.skip(
            "This test must use the testbench emulator; set STORAGE_EMULATOR_HOST to run."
        )

    # Create client to use for setup steps.
    client = storage.Client(client_options={"api_endpoint": host})
    scenario = _CONFORMANCE_TESTS[scenario_id - 1]
    expect_success = scenario["expectSuccess"]
    precondition_provided = scenario["preconditionProvided"]
    json_resources = method["resources"]
    method_name = method["name"]
    instructions = case["instructions"]

    if method_name not in method_mapping:
        pytest.skip("No tests for operation {}".format(method_name),)

    for function in method_mapping[method_name]:
        # Create the retry test in the emulator to handle instructions.
        try:
            r = _create_retry_test(host, method_name, instructions)
            id = r["id"]
        except Exception as e:
            warnings.warn(
                "Error creating retry test for {}: {}".format(method_name, e),
                UserWarning,
                stacklevel=1,
            )
            continue

        # Populate resources.
        try:
            resources = _populate_resources(client, json_resources)
        except Exception as e:
            warnings.warn(
                "Error populating resources for {}: {}".format(method_name, e),
                UserWarning,
                stacklevel=1,
            )
            continue

        # Run retry tests on library methods.
        try:
            _run_retry_test(host, id, function, precondition_provided, **resources)
        except Exception as e:
            print(e)
            success_results = False
        else:
            success_results = True

        # Assert expected success for each scenario.
        assert expect_success == success_results, "Scenario{}-{}: expected_success was {}, should be {}".format(scenario_id, function.__name__, success_results, expect_success)

        # Verify that all instructions were used up during the test
        # (indicates that the client sent the correct requests).
        status_response = _get_retry_test(host, id)
        assert status_response["completed"] is True, "Scenario{}-{}: test not completed; unused instructions:{}".format(scenario_id, function.__name__, status_response["instructions"])

        # Clean up and close out test in emulator.
        _delete_retry_test(host, id)
