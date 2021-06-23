# coding=utf-8

# Copyright 2014 Google LLC
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

import datetime
import os
import unittest

import requests

from google.cloud import exceptions
from google.cloud import storage
from google.cloud.storage._helpers import _base64_md5hash
import google.auth
import google.api_core
import google.oauth2
from test_utils.retry import RetryErrors
from test_utils.retry import RetryInstanceState
from test_utils.system import unique_resource_id


USER_PROJECT = os.environ.get("GOOGLE_CLOUD_TESTS_USER_PROJECT")
DIRNAME = os.path.realpath(os.path.dirname(__file__))
DATA_DIRNAME = os.path.abspath(os.path.join(DIRNAME, "..", "data"))


def _bad_copy(bad_request):
    """Predicate: pass only exceptions for a failed copyTo."""
    err_msg = bad_request.message
    return err_msg.startswith("No file found in request. (POST") and "copyTo" in err_msg


def _no_event_based_hold(blob):
    return not blob.event_based_hold


retry_429 = RetryErrors(exceptions.TooManyRequests, max_tries=6)
retry_429_harder = RetryErrors(exceptions.TooManyRequests, max_tries=10)
retry_429_503 = RetryErrors(
    [exceptions.TooManyRequests, exceptions.ServiceUnavailable], max_tries=10
)
retry_bad_copy = RetryErrors(exceptions.BadRequest, error_predicate=_bad_copy)
retry_no_event_based_hold = RetryInstanceState(_no_event_based_hold)


def _empty_bucket(client, bucket):
    """Empty a bucket of all existing blobs (including multiple versions)."""
    for blob in list(client.list_blobs(bucket, versions=True)):
        try:
            blob.delete()
        except exceptions.NotFound:
            pass


class Config(object):
    """Run-time configuration to be modified at set-up.

    This is a mutable stand-in to allow test set-up to modify
    global state.
    """

    CLIENT = None
    TEST_BUCKET = None
    TESTING_MTLS = False


def setUpModule():
    Config.CLIENT = storage.Client()
    bucket_name = "new" + unique_resource_id()
    # In the **very** rare case the bucket name is reserved, this
    # fails with a ConnectionError.
    Config.TEST_BUCKET = Config.CLIENT.bucket(bucket_name)
    Config.TEST_BUCKET.versioning_enabled = True
    retry_429_503(Config.TEST_BUCKET.create)()
    # mTLS testing uses the system test as well. For mTLS testing,
    # GOOGLE_API_USE_CLIENT_CERTIFICATE env var will be set to "true"
    # explicitly.
    Config.TESTING_MTLS = os.getenv("GOOGLE_API_USE_CLIENT_CERTIFICATE") == "true"


def tearDownModule():
    errors = (exceptions.Conflict, exceptions.TooManyRequests)
    retry = RetryErrors(errors, max_tries=15)
    retry(_empty_bucket)(Config.CLIENT, Config.TEST_BUCKET)
    retry(Config.TEST_BUCKET.delete)(force=True)


class TestRetentionPolicy(unittest.TestCase):
    def setUp(self):
        self.case_buckets_to_delete = []
        self.case_blobs_to_delete = []

    def tearDown(self):
        # discard test blobs retention policy settings
        for blob in self.case_blobs_to_delete:
            blob.event_based_hold = False
            blob.temporary_hold = False
            blob.patch()

        for bucket_name in self.case_buckets_to_delete:
            bucket = Config.CLIENT.bucket(bucket_name)
            retry_429_harder(bucket.delete)(force=True)

    def test_bucket_w_retention_period(self):
        import datetime
        from google.api_core import exceptions

        period_secs = 10

        new_bucket_name = "w-retention-period" + unique_resource_id("-")
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)

        bucket.retention_period = period_secs
        bucket.default_event_based_hold = False
        bucket.patch()

        self.assertEqual(bucket.retention_period, period_secs)
        self.assertIsInstance(bucket.retention_policy_effective_time, datetime.datetime)
        self.assertFalse(bucket.default_event_based_hold)
        self.assertFalse(bucket.retention_policy_locked)

        blob_name = "test-blob"
        payload = b"DEADBEEF"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(payload)

        self.case_blobs_to_delete.append(blob)

        other = bucket.get_blob(blob_name)

        self.assertFalse(other.event_based_hold)
        self.assertFalse(other.temporary_hold)
        self.assertIsInstance(other.retention_expiration_time, datetime.datetime)

        with self.assertRaises(exceptions.Forbidden):
            other.delete()

        bucket.retention_period = None
        bucket.patch()

        self.assertIsNone(bucket.retention_period)
        self.assertIsNone(bucket.retention_policy_effective_time)
        self.assertFalse(bucket.default_event_based_hold)
        self.assertFalse(bucket.retention_policy_locked)

        other.reload()

        self.assertFalse(other.event_based_hold)
        self.assertFalse(other.temporary_hold)
        self.assertIsNone(other.retention_expiration_time)

        other.delete()
        self.case_blobs_to_delete.pop()

    def test_bucket_w_default_event_based_hold(self):
        from google.api_core import exceptions

        new_bucket_name = "w-def-ebh" + unique_resource_id("-")
        self.assertRaises(
            exceptions.NotFound, Config.CLIENT.get_bucket, new_bucket_name
        )
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)

        bucket.default_event_based_hold = True
        bucket.patch()

        self.assertTrue(bucket.default_event_based_hold)
        self.assertIsNone(bucket.retention_period)
        self.assertIsNone(bucket.retention_policy_effective_time)
        self.assertFalse(bucket.retention_policy_locked)

        blob_name = "test-blob"
        payload = b"DEADBEEF"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(payload)

        self.case_blobs_to_delete.append(blob)

        other = bucket.get_blob(blob_name)

        self.assertTrue(other.event_based_hold)
        self.assertFalse(other.temporary_hold)
        self.assertIsNone(other.retention_expiration_time)

        with self.assertRaises(exceptions.Forbidden):
            other.delete()

        other.event_based_hold = False
        other.patch()
        other.delete()

        bucket.default_event_based_hold = False
        bucket.patch()

        self.assertFalse(bucket.default_event_based_hold)
        self.assertIsNone(bucket.retention_period)
        self.assertIsNone(bucket.retention_policy_effective_time)
        self.assertFalse(bucket.retention_policy_locked)

        blob.upload_from_string(payload)

        # https://github.com/googleapis/python-storage/issues/435
        if blob.event_based_hold:
            retry_no_event_based_hold(blob.reload)()

        self.assertFalse(blob.event_based_hold)
        self.assertFalse(blob.temporary_hold)
        self.assertIsNone(blob.retention_expiration_time)

        blob.delete()
        self.case_blobs_to_delete.pop()

    def test_blob_w_temporary_hold(self):
        from google.api_core import exceptions

        new_bucket_name = "w-tmp-hold" + unique_resource_id("-")
        self.assertRaises(
            exceptions.NotFound, Config.CLIENT.get_bucket, new_bucket_name
        )
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)

        blob_name = "test-blob"
        payload = b"DEADBEEF"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(payload)

        self.case_blobs_to_delete.append(blob)

        other = bucket.get_blob(blob_name)
        other.temporary_hold = True
        other.patch()

        self.assertTrue(other.temporary_hold)
        self.assertFalse(other.event_based_hold)
        self.assertIsNone(other.retention_expiration_time)

        with self.assertRaises(exceptions.Forbidden):
            other.delete()

        other.temporary_hold = False
        other.patch()

        other.delete()
        self.case_blobs_to_delete.pop()

    def test_bucket_lock_retention_policy(self):
        import datetime
        from google.api_core import exceptions

        period_secs = 10

        new_bucket_name = "loc-ret-policy" + unique_resource_id("-")
        self.assertRaises(
            exceptions.NotFound, Config.CLIENT.get_bucket, new_bucket_name
        )
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)

        bucket.retention_period = period_secs
        bucket.patch()

        self.assertEqual(bucket.retention_period, period_secs)
        self.assertIsInstance(bucket.retention_policy_effective_time, datetime.datetime)
        self.assertFalse(bucket.default_event_based_hold)
        self.assertFalse(bucket.retention_policy_locked)

        bucket.lock_retention_policy()

        bucket.reload()
        self.assertTrue(bucket.retention_policy_locked)

        bucket.retention_period = None
        with self.assertRaises(exceptions.Forbidden):
            bucket.patch()


class TestIAMConfiguration(unittest.TestCase):
    def setUp(self):
        self.case_buckets_to_delete = []

    def tearDown(self):
        for bucket_name in self.case_buckets_to_delete:
            bucket = Config.CLIENT.bucket(bucket_name)
            retry_429_harder(bucket.delete)(force=True)

    def test_new_bucket_w_ubla(self):
        new_bucket_name = "new-w-ubla" + unique_resource_id("-")
        self.assertRaises(
            exceptions.NotFound, Config.CLIENT.get_bucket, new_bucket_name
        )
        bucket = Config.CLIENT.bucket(new_bucket_name)
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        retry_429_503(bucket.create)()
        self.case_buckets_to_delete.append(new_bucket_name)

        bucket_acl = bucket.acl
        with self.assertRaises(exceptions.BadRequest):
            bucket_acl.reload()

        bucket_acl.loaded = True  # Fake that we somehow loaded the ACL
        bucket_acl.all().grant_read()
        with self.assertRaises(exceptions.BadRequest):
            bucket_acl.save()

        blob_name = "my-blob.txt"
        blob = bucket.blob(blob_name)
        payload = b"DEADBEEF"
        blob.upload_from_string(payload)

        found = bucket.get_blob(blob_name)
        self.assertEqual(found.download_as_bytes(), payload)

        blob_acl = blob.acl
        with self.assertRaises(exceptions.BadRequest):
            blob_acl.reload()

        blob_acl.loaded = True  # Fake that we somehow loaded the ACL
        blob_acl.all().grant_read()
        with self.assertRaises(exceptions.BadRequest):
            blob_acl.save()

    def test_ubla_set_unset_preserves_acls(self):
        new_bucket_name = "ubla-acls" + unique_resource_id("-")
        self.assertRaises(
            exceptions.NotFound, Config.CLIENT.get_bucket, new_bucket_name
        )
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)

        blob_name = "my-blob.txt"
        blob = bucket.blob(blob_name)
        payload = b"DEADBEEF"
        blob.upload_from_string(payload)

        # Preserve ACLs before setting UBLA
        bucket_acl_before = list(bucket.acl)
        blob_acl_before = list(bucket.acl)

        # Set UBLA
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket.patch()

        self.assertTrue(bucket.iam_configuration.uniform_bucket_level_access_enabled)

        # While UBLA is set, cannot get / set ACLs
        with self.assertRaises(exceptions.BadRequest):
            bucket.acl.reload()

        # Clear UBLA
        bucket.iam_configuration.uniform_bucket_level_access_enabled = False
        bucket.patch()

        # Query ACLs after clearing UBLA
        bucket.acl.reload()
        bucket_acl_after = list(bucket.acl)
        blob.acl.reload()
        blob_acl_after = list(bucket.acl)

        self.assertEqual(bucket_acl_before, bucket_acl_after)
        self.assertEqual(blob_acl_before, blob_acl_after)


class TestV4POSTPolicies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestV4POSTPolicies, cls).setUpClass()
        if (
            type(Config.CLIENT._credentials)
            is not google.oauth2.service_account.Credentials
        ):
            # mTLS only works for user credentials, it doesn't work for
            # service account credentials.
            raise unittest.SkipTest("These tests require a service account credential")

    def setUp(self):
        self.case_buckets_to_delete = []

    def tearDown(self):
        for bucket_name in self.case_buckets_to_delete:
            bucket = Config.CLIENT.bucket(bucket_name)
            retry_429_harder(bucket.delete)(force=True)

    def test_get_signed_policy_v4(self):
        bucket_name = "post_policy" + unique_resource_id("-")
        self.assertRaises(exceptions.NotFound, Config.CLIENT.get_bucket, bucket_name)
        retry_429_503(Config.CLIENT.create_bucket)(bucket_name)
        self.case_buckets_to_delete.append(bucket_name)

        blob_name = "post_policy_obj.txt"
        with open(blob_name, "w") as f:
            f.write("DEADBEEF")

        policy = Config.CLIENT.generate_signed_post_policy_v4(
            bucket_name,
            blob_name,
            conditions=[
                {"bucket": bucket_name},
                ["starts-with", "$Content-Type", "text/pla"],
            ],
            expiration=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            fields={"content-type": "text/plain"},
        )
        with open(blob_name, "r") as f:
            files = {"file": (blob_name, f)}
            response = requests.post(policy["url"], data=policy["fields"], files=files)

        os.remove(blob_name)
        self.assertEqual(response.status_code, 204)

    def test_get_signed_policy_v4_invalid_field(self):
        bucket_name = "post_policy" + unique_resource_id("-")
        self.assertRaises(exceptions.NotFound, Config.CLIENT.get_bucket, bucket_name)
        retry_429_503(Config.CLIENT.create_bucket)(bucket_name)
        self.case_buckets_to_delete.append(bucket_name)

        blob_name = "post_policy_obj.txt"
        with open(blob_name, "w") as f:
            f.write("DEADBEEF")

        policy = Config.CLIENT.generate_signed_post_policy_v4(
            bucket_name,
            blob_name,
            conditions=[
                {"bucket": bucket_name},
                ["starts-with", "$Content-Type", "text/pla"],
            ],
            expiration=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            fields={"x-goog-random": "invalid_field", "content-type": "text/plain"},
        )
        with open(blob_name, "r") as f:
            files = {"file": (blob_name, f)}
            response = requests.post(policy["url"], data=policy["fields"], files=files)

        os.remove(blob_name)
        self.assertEqual(response.status_code, 400)
