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
from google.cloud.storage import _helpers

from . import _read_local_json

import pytest
import requests
import warnings


_CONFORMANCE_TESTS = _read_local_json("retry_strategy_test_data.json")[
    "retryStrategyTests"
]

_API_ACCESS_ENDPOINT = _helpers._get_storage_host()
_DEFAULT_STORAGE_HOST = u"https://storage.googleapis.com"
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
        break


def list_blobs(client, _preconditions, bucket, **_):
    blobs = client.list_blobs(bucket.name)
    for b in blobs:
        break


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
        break


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
        break


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
    import json

    preflight_post_uri = host + "/retry_test"
    headers = {
        "Content-Type": "application/json",
    }
    data_dict = {"instructions": {method_name: instructions}}
    data = json.dumps(data_dict)
    r = requests.post(preflight_post_uri, headers=headers, data=data)
    return r.json()


def _check_retry_test(host, id):
    status_get_uri = "{base}{retry}/{id}".format(base=host, retry="/retry_test", id=id)
    r = requests.get(status_get_uri)
    return r.json()


def _run_retry_test(host, id, func, _preconditions, **resources):
    # Create client using x-retry-test-id header.
    client = storage.Client(client_options={"api_endpoint": host})
    client._http.headers.update({"x-retry-test-id": id})
    func(client, _preconditions, **resources)


def _delete_retry_test(host, id):
    status_get_uri = "{base}{retry}/{id}".format(base=host, retry="/retry_test", id=id)
    requests.delete(status_get_uri)


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
    client = storage.Client(client_options={"api_endpoint": host})
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
                warnings.warn(
                    "No tests for operation {}".format(method_name),
                    UserWarning,
                    stacklevel=1,
                )
                continue

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
                    _run_retry_test(
                        host, id, function, precondition_provided, **resources
                    )
                except Exception as e:
                    # Should we be catching specific exceptions
                    print(e)
                    success_results = False
                else:
                    success_results = True

                # Assert expected success for each scenario.
                assert expect_success == success_results

                # Verify that all instructions were used up during the test
                # (indicates that the client sent the correct requests).
                try:
                    status_response = _check_retry_test(host, id)
                    assert status_response["completed"] is True
                except Exception as e:
                    warnings.warn(
                        "Error checking retry test status for {}: {}".format(
                            method_name, e
                        ),
                        UserWarning,
                        stacklevel=1,
                    )

                # Clean up and close out test in emulator.
                try:
                    _delete_retry_test(host, id)
                except Exception as e:
                    warnings.warn(
                        "Error deleting retry test for {}: {}".format(method_name, e),
                        UserWarning,
                        stacklevel=1,
                    )
