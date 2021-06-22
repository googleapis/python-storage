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
import tempfile
import time
import unittest

import requests

from google.cloud import exceptions
from google.cloud import storage
from google.cloud.storage._helpers import _base64_md5hash
from google.cloud import kms
import google.auth
import google.api_core
import google.oauth2
from test_utils.retry import RetryErrors
from test_utils.retry import RetryInstanceState
from test_utils.system import unique_resource_id
from test_utils.vpcsc_config import vpcsc_config


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


class TestStorageFiles(unittest.TestCase):

    FILES = {
        "logo": {"path": os.path.join(DATA_DIRNAME, "CloudPlatform_128px_Retina.png")},
        "big": {"path": os.path.join(DATA_DIRNAME, "five-point-one-mb-file.zip")},
        "simple": {"path": os.path.join(DATA_DIRNAME, "simple.txt")},
    }

    @classmethod
    def setUpClass(cls):
        super(TestStorageFiles, cls).setUpClass()
        for file_data in cls.FILES.values():
            with open(file_data["path"], "rb") as file_obj:
                file_data["hash"] = _base64_md5hash(file_obj)
        cls.bucket = Config.TEST_BUCKET

    def setUp(self):
        self.case_blobs_to_delete = []

    def tearDown(self):
        errors = (exceptions.TooManyRequests, exceptions.ServiceUnavailable)
        retry = RetryErrors(errors, max_tries=6)
        for blob in self.case_blobs_to_delete:
            retry(blob.delete)()


class TestStorageSignURLs(unittest.TestCase):
    BLOB_CONTENT = b"This time for sure, Rocky!"

    @classmethod
    def setUpClass(cls):
        super(TestStorageSignURLs, cls).setUpClass()
        if (
            type(Config.CLIENT._credentials)
            is not google.oauth2.service_account.Credentials
        ):
            raise unittest.SkipTest(
                "Signing tests requires a service account credential"
            )

        bucket_name = "gcp-signing" + unique_resource_id()
        cls.bucket = retry_429_503(Config.CLIENT.create_bucket)(bucket_name)
        cls.blob = cls.bucket.blob("README.txt")
        cls.blob.upload_from_string(cls.BLOB_CONTENT)

    @classmethod
    def tearDownClass(cls):
        _empty_bucket(Config.CLIENT, cls.bucket)
        errors = (exceptions.Conflict, exceptions.TooManyRequests)
        retry = RetryErrors(errors, max_tries=6)
        retry(cls.bucket.delete)(force=True)

    @staticmethod
    def _morph_expiration(version, expiration):
        if expiration is not None:
            return expiration

        if version == "v2":
            return int(time.time()) + 10

        return 10

    def _signed_resumable_upload_url_helper(self, version="v2", expiration=None):
        expiration = self._morph_expiration(version, expiration)
        blob = self.bucket.blob("cruddy.txt")
        payload = b"DEADBEEF"

        # Initiate the upload using a signed URL.
        signed_resumable_upload_url = blob.generate_signed_url(
            expiration=expiration,
            method="RESUMABLE",
            client=Config.CLIENT,
            version=version,
        )

        post_headers = {"x-goog-resumable": "start"}
        post_response = requests.post(signed_resumable_upload_url, headers=post_headers)
        self.assertEqual(post_response.status_code, 201)

        # Finish uploading the body.
        location = post_response.headers["Location"]
        put_headers = {"content-length": str(len(payload))}
        put_response = requests.put(location, headers=put_headers, data=payload)
        self.assertEqual(put_response.status_code, 200)

        # Download using a signed URL and verify.
        signed_download_url = blob.generate_signed_url(
            expiration=expiration, method="GET", client=Config.CLIENT, version=version
        )

        get_response = requests.get(signed_download_url)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.content, payload)

        # Finally, delete the blob using a signed URL.
        signed_delete_url = blob.generate_signed_url(
            expiration=expiration,
            method="DELETE",
            client=Config.CLIENT,
            version=version,
        )

        delete_response = requests.delete(signed_delete_url)
        self.assertEqual(delete_response.status_code, 204)

    def test_signed_resumable_upload_url_v2(self):
        self._signed_resumable_upload_url_helper(version="v2")

    def test_signed_resumable_upload_url_v4(self):
        self._signed_resumable_upload_url_helper(version="v4")


class TestStorageCompose(TestStorageFiles):

    FILES = {}

    def test_compose_create_new_blob(self):
        SOURCE_1 = b"AAA\n"
        source_1 = self.bucket.blob("source-1")
        source_1.upload_from_string(SOURCE_1)
        self.case_blobs_to_delete.append(source_1)

        SOURCE_2 = b"BBB\n"
        source_2 = self.bucket.blob("source-2")
        source_2.upload_from_string(SOURCE_2)
        self.case_blobs_to_delete.append(source_2)

        destination = self.bucket.blob("destination")
        destination.content_type = "text/plain"
        destination.compose([source_1, source_2])
        self.case_blobs_to_delete.append(destination)

        composed = destination.download_as_bytes()
        self.assertEqual(composed, SOURCE_1 + SOURCE_2)

    def test_compose_create_new_blob_wo_content_type(self):
        SOURCE_1 = b"AAA\n"
        source_1 = self.bucket.blob("source-1")
        source_1.upload_from_string(SOURCE_1)
        self.case_blobs_to_delete.append(source_1)

        SOURCE_2 = b"BBB\n"
        source_2 = self.bucket.blob("source-2")
        source_2.upload_from_string(SOURCE_2)
        self.case_blobs_to_delete.append(source_2)

        destination = self.bucket.blob("destination")

        destination.compose([source_1, source_2])
        self.case_blobs_to_delete.append(destination)

        self.assertIsNone(destination.content_type)
        composed = destination.download_as_bytes()
        self.assertEqual(composed, SOURCE_1 + SOURCE_2)

    def test_compose_replace_existing_blob(self):
        BEFORE = b"AAA\n"
        original = self.bucket.blob("original")
        original.content_type = "text/plain"
        original.upload_from_string(BEFORE)
        self.case_blobs_to_delete.append(original)

        TO_APPEND = b"BBB\n"
        to_append = self.bucket.blob("to_append")
        to_append.upload_from_string(TO_APPEND)
        self.case_blobs_to_delete.append(to_append)

        original.compose([original, to_append])

        composed = original.download_as_bytes()
        self.assertEqual(composed, BEFORE + TO_APPEND)

    def test_compose_with_generation_match_list(self):
        BEFORE = b"AAA\n"
        original = self.bucket.blob("original")
        original.content_type = "text/plain"
        original.upload_from_string(BEFORE)
        self.case_blobs_to_delete.append(original)

        TO_APPEND = b"BBB\n"
        to_append = self.bucket.blob("to_append")
        to_append.upload_from_string(TO_APPEND)
        self.case_blobs_to_delete.append(to_append)

        with self.assertRaises(google.api_core.exceptions.PreconditionFailed):
            original.compose(
                [original, to_append],
                if_generation_match=[6, 7],
                if_metageneration_match=[8, 9],
            )

        original.compose(
            [original, to_append],
            if_generation_match=[original.generation, to_append.generation],
            if_metageneration_match=[original.metageneration, to_append.metageneration],
        )

        composed = original.download_as_bytes()
        self.assertEqual(composed, BEFORE + TO_APPEND)

    def test_compose_with_generation_match_long(self):
        BEFORE = b"AAA\n"
        original = self.bucket.blob("original")
        original.content_type = "text/plain"
        original.upload_from_string(BEFORE)
        self.case_blobs_to_delete.append(original)

        TO_APPEND = b"BBB\n"
        to_append = self.bucket.blob("to_append")
        to_append.upload_from_string(TO_APPEND)
        self.case_blobs_to_delete.append(to_append)

        with self.assertRaises(google.api_core.exceptions.PreconditionFailed):
            original.compose([original, to_append], if_generation_match=0)

        original.compose([original, to_append], if_generation_match=original.generation)

        composed = original.download_as_bytes()
        self.assertEqual(composed, BEFORE + TO_APPEND)

    def test_compose_with_source_generation_match(self):
        BEFORE = b"AAA\n"
        original = self.bucket.blob("original")
        original.content_type = "text/plain"
        original.upload_from_string(BEFORE)
        self.case_blobs_to_delete.append(original)

        TO_APPEND = b"BBB\n"
        to_append = self.bucket.blob("to_append")
        to_append.upload_from_string(TO_APPEND)
        self.case_blobs_to_delete.append(to_append)

        with self.assertRaises(google.api_core.exceptions.PreconditionFailed):
            original.compose([original, to_append], if_source_generation_match=[6, 7])

        original.compose(
            [original, to_append],
            if_source_generation_match=[original.generation, to_append.generation],
        )

        composed = original.download_as_bytes()
        self.assertEqual(composed, BEFORE + TO_APPEND)

    @unittest.skipUnless(USER_PROJECT, "USER_PROJECT not set in environment.")
    def test_compose_with_user_project(self):
        new_bucket_name = "compose-user-project" + unique_resource_id("-")
        created = retry_429_503(Config.CLIENT.create_bucket)(
            new_bucket_name, requester_pays=True
        )
        try:
            SOURCE_1 = b"AAA\n"
            source_1 = created.blob("source-1")
            source_1.upload_from_string(SOURCE_1)

            SOURCE_2 = b"BBB\n"
            source_2 = created.blob("source-2")
            source_2.upload_from_string(SOURCE_2)

            with_user_project = Config.CLIENT.bucket(
                new_bucket_name, user_project=USER_PROJECT
            )

            destination = with_user_project.blob("destination")
            destination.content_type = "text/plain"
            destination.compose([source_1, source_2])

            composed = destination.download_as_bytes()
            self.assertEqual(composed, SOURCE_1 + SOURCE_2)
        finally:
            retry_429_harder(created.delete)(force=True)


class TestStorageRewrite(TestStorageFiles):

    FILENAMES = ("file01.txt",)

    def test_rewrite_create_new_blob_add_encryption_key(self):
        file_data = self.FILES["simple"]

        source = self.bucket.blob("source")
        source.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(source)
        source_data = source.download_as_bytes()

        KEY = os.urandom(32)
        dest = self.bucket.blob("dest", encryption_key=KEY)
        token, rewritten, total = dest.rewrite(source)
        self.case_blobs_to_delete.append(dest)

        self.assertEqual(token, None)
        self.assertEqual(rewritten, len(source_data))
        self.assertEqual(total, len(source_data))

        self.assertEqual(source.download_as_bytes(), dest.download_as_bytes())

    def test_rewrite_rotate_encryption_key(self):
        BLOB_NAME = "rotating-keys"
        file_data = self.FILES["simple"]

        SOURCE_KEY = os.urandom(32)
        source = self.bucket.blob(BLOB_NAME, encryption_key=SOURCE_KEY)
        source.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(source)
        source_data = source.download_as_bytes()

        DEST_KEY = os.urandom(32)
        dest = self.bucket.blob(BLOB_NAME, encryption_key=DEST_KEY)
        token, rewritten, total = dest.rewrite(source)
        # Not adding 'dest' to 'self.case_blobs_to_delete':  it is the
        # same object as 'source'.

        self.assertIsNone(token)
        self.assertEqual(rewritten, len(source_data))
        self.assertEqual(total, len(source_data))

        self.assertEqual(dest.download_as_bytes(), source_data)

    @unittest.skipUnless(USER_PROJECT, "USER_PROJECT not set in environment.")
    def test_rewrite_add_key_with_user_project(self):
        file_data = self.FILES["simple"]
        new_bucket_name = "rewrite-key-up" + unique_resource_id("-")
        created = retry_429_503(Config.CLIENT.create_bucket)(
            new_bucket_name, requester_pays=True
        )
        try:
            with_user_project = Config.CLIENT.bucket(
                new_bucket_name, user_project=USER_PROJECT
            )

            source = with_user_project.blob("source")
            source.upload_from_filename(file_data["path"])
            source_data = source.download_as_bytes()

            KEY = os.urandom(32)
            dest = with_user_project.blob("dest", encryption_key=KEY)
            token, rewritten, total = dest.rewrite(source)

            self.assertEqual(token, None)
            self.assertEqual(rewritten, len(source_data))
            self.assertEqual(total, len(source_data))

            self.assertEqual(source.download_as_bytes(), dest.download_as_bytes())
        finally:
            retry_429_harder(created.delete)(force=True)

    @unittest.skipUnless(USER_PROJECT, "USER_PROJECT not set in environment.")
    def test_rewrite_rotate_with_user_project(self):
        BLOB_NAME = "rotating-keys"
        file_data = self.FILES["simple"]
        new_bucket_name = "rewrite-rotate-up" + unique_resource_id("-")
        created = retry_429_503(Config.CLIENT.create_bucket)(
            new_bucket_name, requester_pays=True
        )
        try:
            with_user_project = Config.CLIENT.bucket(
                new_bucket_name, user_project=USER_PROJECT
            )

            SOURCE_KEY = os.urandom(32)
            source = with_user_project.blob(BLOB_NAME, encryption_key=SOURCE_KEY)
            source.upload_from_filename(file_data["path"])
            source_data = source.download_as_bytes()

            DEST_KEY = os.urandom(32)
            dest = with_user_project.blob(BLOB_NAME, encryption_key=DEST_KEY)
            token, rewritten, total = dest.rewrite(source)

            self.assertEqual(token, None)
            self.assertEqual(rewritten, len(source_data))
            self.assertEqual(total, len(source_data))

            self.assertEqual(dest.download_as_bytes(), source_data)
        finally:
            retry_429_harder(created.delete)(force=True)

    def test_rewrite_with_generation_match(self):
        WRONG_GENERATION_NUMBER = 6
        BLOB_NAME = "generation-match"

        file_data = self.FILES["simple"]
        new_bucket_name = "rewrite-generation-match" + unique_resource_id("-")
        created = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        try:
            bucket = Config.CLIENT.bucket(new_bucket_name)

            source = bucket.blob(BLOB_NAME)
            source.upload_from_filename(file_data["path"])
            source_data = source.download_as_bytes()

            dest = bucket.blob(BLOB_NAME)

            with self.assertRaises(google.api_core.exceptions.PreconditionFailed):
                token, rewritten, total = dest.rewrite(
                    source, if_generation_match=WRONG_GENERATION_NUMBER
                )

            token, rewritten, total = dest.rewrite(
                source,
                if_generation_match=dest.generation,
                if_source_generation_match=source.generation,
                if_source_metageneration_match=source.metageneration,
            )
            self.assertEqual(token, None)
            self.assertEqual(rewritten, len(source_data))
            self.assertEqual(total, len(source_data))
            self.assertEqual(dest.download_as_bytes(), source_data)
        finally:
            retry_429_harder(created.delete)(force=True)


class TestStorageUpdateStorageClass(TestStorageFiles):
    def test_update_storage_class_small_file(self):
        from google.cloud.storage import constants

        blob = self.bucket.blob("SmallFile")

        file_data = self.FILES["simple"]
        blob.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(blob)

        blob.update_storage_class(constants.NEARLINE_STORAGE_CLASS)
        blob.reload()
        self.assertEqual(blob.storage_class, constants.NEARLINE_STORAGE_CLASS)

        blob.update_storage_class(constants.COLDLINE_STORAGE_CLASS)
        blob.reload()
        self.assertEqual(blob.storage_class, constants.COLDLINE_STORAGE_CLASS)

    def test_update_storage_class_large_file(self):
        from google.cloud.storage import constants

        blob = self.bucket.blob("BigFile")

        file_data = self.FILES["big"]
        blob.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(blob)

        blob.update_storage_class(constants.NEARLINE_STORAGE_CLASS)
        blob.reload()
        self.assertEqual(blob.storage_class, constants.NEARLINE_STORAGE_CLASS)

        blob.update_storage_class(constants.COLDLINE_STORAGE_CLASS)
        blob.reload()
        self.assertEqual(blob.storage_class, constants.COLDLINE_STORAGE_CLASS)


class TestStorageNotificationCRUD(unittest.TestCase):

    topic = None
    TOPIC_NAME = "notification" + unique_resource_id("-")
    CUSTOM_ATTRIBUTES = {"attr1": "value1", "attr2": "value2"}
    BLOB_NAME_PREFIX = "blob-name-prefix/"

    @classmethod
    def setUpClass(cls):
        super(TestStorageNotificationCRUD, cls).setUpClass()
        if Config.TESTING_MTLS:
            # mTLS is only available for python-pubsub >= 2.2.0. However, the
            # system test uses python-pubsub < 2.0, so we skip those tests.
            # Note that python-pubsub >= 2.0 no longer supports python 2.7, so
            # we can only upgrade it after python 2.7 system test is removed.
            # Since python-pubsub >= 2.0 has a new set of api, the test code
            # also needs to be updated.
            raise unittest.SkipTest("Skip pubsub tests for mTLS testing")

    @property
    def topic_path(self):
        return "projects/{}/topics/{}".format(Config.CLIENT.project, self.TOPIC_NAME)

    def _initialize_topic(self):
        try:
            from google.cloud.pubsub_v1 import PublisherClient
        except ImportError:
            raise unittest.SkipTest("Cannot import pubsub")
        self.publisher_client = PublisherClient()
        retry_429(self.publisher_client.create_topic)(self.topic_path)
        policy = self.publisher_client.get_iam_policy(self.topic_path)
        binding = policy.bindings.add()
        binding.role = "roles/pubsub.publisher"
        binding.members.append(
            "serviceAccount:{}".format(Config.CLIENT.get_service_account_email())
        )
        self.publisher_client.set_iam_policy(self.topic_path, policy)

    def setUp(self):
        self.case_buckets_to_delete = []
        self._initialize_topic()

    def tearDown(self):
        retry_429(self.publisher_client.delete_topic)(self.topic_path)
        with Config.CLIENT.batch():
            for bucket_name in self.case_buckets_to_delete:
                bucket = Config.CLIENT.bucket(bucket_name)
                retry_429_harder(bucket.delete)()

    @staticmethod
    def event_types():
        from google.cloud.storage.notification import (
            OBJECT_FINALIZE_EVENT_TYPE,
            OBJECT_DELETE_EVENT_TYPE,
        )

        return [OBJECT_FINALIZE_EVENT_TYPE, OBJECT_DELETE_EVENT_TYPE]

    @staticmethod
    def payload_format():
        from google.cloud.storage.notification import JSON_API_V1_PAYLOAD_FORMAT

        return JSON_API_V1_PAYLOAD_FORMAT

    def test_notification_minimal(self):
        new_bucket_name = "notification-minimal" + unique_resource_id("-")
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)
        self.assertEqual(list(bucket.list_notifications()), [])

        notification = bucket.notification(self.TOPIC_NAME)
        retry_429_503(notification.create)()
        try:
            self.assertTrue(notification.exists())
            self.assertIsNotNone(notification.notification_id)
            notifications = list(bucket.list_notifications())
            self.assertEqual(len(notifications), 1)
            self.assertEqual(notifications[0].topic_name, self.TOPIC_NAME)
        finally:
            notification.delete()

    def test_notification_explicit(self):
        new_bucket_name = "notification-explicit" + unique_resource_id("-")
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)
        notification = bucket.notification(
            topic_name=self.TOPIC_NAME,
            custom_attributes=self.CUSTOM_ATTRIBUTES,
            event_types=self.event_types(),
            blob_name_prefix=self.BLOB_NAME_PREFIX,
            payload_format=self.payload_format(),
        )
        retry_429_503(notification.create)()
        try:
            self.assertTrue(notification.exists())
            self.assertIsNotNone(notification.notification_id)
            self.assertEqual(notification.custom_attributes, self.CUSTOM_ATTRIBUTES)
            self.assertEqual(notification.event_types, self.event_types())
            self.assertEqual(notification.blob_name_prefix, self.BLOB_NAME_PREFIX)
            self.assertEqual(notification.payload_format, self.payload_format())

        finally:
            notification.delete()

    @unittest.skipUnless(USER_PROJECT, "USER_PROJECT not set in environment.")
    def test_notification_w_user_project(self):
        new_bucket_name = "notification-minimal" + unique_resource_id("-")
        retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name, requester_pays=True)
        self.case_buckets_to_delete.append(new_bucket_name)
        with_user_project = Config.CLIENT.bucket(
            new_bucket_name, user_project=USER_PROJECT
        )
        self.assertEqual(list(with_user_project.list_notifications()), [])
        notification = with_user_project.notification(self.TOPIC_NAME)
        retry_429(notification.create)()
        try:
            self.assertTrue(notification.exists())
            self.assertIsNotNone(notification.notification_id)
            notifications = list(with_user_project.list_notifications())
            self.assertEqual(len(notifications), 1)
            self.assertEqual(notifications[0].topic_name, self.TOPIC_NAME)
        finally:
            notification.delete()

    def test_get_notification(self):
        new_bucket_name = "get-notification" + unique_resource_id("-")
        bucket = retry_429_503(Config.CLIENT.create_bucket)(new_bucket_name)
        self.case_buckets_to_delete.append(new_bucket_name)

        notification = bucket.notification(
            topic_name=self.TOPIC_NAME,
            custom_attributes=self.CUSTOM_ATTRIBUTES,
            payload_format=self.payload_format(),
        )
        retry_429_503(notification.create)()
        try:
            self.assertTrue(notification.exists())
            self.assertIsNotNone(notification.notification_id)
            notification_id = notification.notification_id
            notification = bucket.get_notification(notification_id)
            self.assertEqual(notification.notification_id, notification_id)
            self.assertEqual(notification.custom_attributes, self.CUSTOM_ATTRIBUTES)
            self.assertEqual(notification.payload_format, self.payload_format())
        finally:
            notification.delete()


class TestAnonymousClient(unittest.TestCase):

    PUBLIC_BUCKET = "gcp-public-data-landsat"

    @vpcsc_config.skip_if_inside_vpcsc
    def test_access_to_public_bucket(self):
        anonymous = storage.Client.create_anonymous_client()
        bucket = anonymous.bucket(self.PUBLIC_BUCKET)
        (blob,) = retry_429_503(anonymous.list_blobs)(bucket, max_results=1)
        with tempfile.TemporaryFile() as stream:
            retry_429_503(blob.download_to_file)(stream)


class TestKMSIntegration(TestStorageFiles):

    FILENAMES = ("file01.txt",)

    KEYRING_NAME = "gcs-test"
    KEY_NAME = "gcs-test"
    ALT_KEY_NAME = "gcs-test-alternate"

    def _kms_key_name(self, key_name=None):
        if key_name is None:
            key_name = self.KEY_NAME

        return ("projects/{}/" "locations/{}/" "keyRings/{}/" "cryptoKeys/{}").format(
            Config.CLIENT.project,
            self.bucket.location.lower(),
            self.KEYRING_NAME,
            key_name,
        )

    @classmethod
    def setUpClass(cls):
        super(TestKMSIntegration, cls).setUpClass()
        if Config.TESTING_MTLS:
            # mTLS is only available for python-kms >= 2.2.0. However, the
            # system test uses python-kms < 2.0, so we skip those tests.
            # Note that python-kms >= 2.0 no longer supports python 2.7, so
            # we can only upgrade it after python 2.7 system test is removed.
            # Since python-kms >= 2.0 has a new set of api, the test code
            # also needs to be updated.
            raise unittest.SkipTest("Skip kms tests for mTLS testing")

        _empty_bucket(Config.CLIENT, cls.bucket)

    def setUp(self):
        super(TestKMSIntegration, self).setUp()
        client = kms.KeyManagementServiceClient()
        project = Config.CLIENT.project
        location = self.bucket.location.lower()
        keyring_name = self.KEYRING_NAME
        purpose = kms.enums.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT

        # If the keyring doesn't exist create it.
        keyring_path = client.key_ring_path(project, location, keyring_name)

        try:
            client.get_key_ring(keyring_path)
        except exceptions.NotFound:
            parent = client.location_path(project, location)
            client.create_key_ring(parent, keyring_name, {})

            # Mark this service account as an owner of the new keyring
            service_account = Config.CLIENT.get_service_account_email()
            policy = {
                "bindings": [
                    {
                        "role": "roles/cloudkms.cryptoKeyEncrypterDecrypter",
                        "members": ["serviceAccount:" + service_account],
                    }
                ]
            }
            client.set_iam_policy(keyring_path, policy)

        # Populate the keyring with the keys we use in the tests
        key_names = [
            "gcs-test",
            "gcs-test-alternate",
            "explicit-kms-key-name",
            "default-kms-key-name",
            "override-default-kms-key-name",
            "alt-default-kms-key-name",
        ]
        for key_name in key_names:
            key_path = client.crypto_key_path(project, location, keyring_name, key_name)
            try:
                client.get_crypto_key(key_path)
            except exceptions.NotFound:
                key = {"purpose": purpose}
                client.create_crypto_key(keyring_path, key_name, key)

    def test_blob_w_explicit_kms_key_name(self):
        BLOB_NAME = "explicit-kms-key-name"
        file_data = self.FILES["simple"]
        kms_key_name = self._kms_key_name()
        blob = self.bucket.blob(BLOB_NAME, kms_key_name=kms_key_name)
        blob.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(blob)
        with open(file_data["path"], "rb") as _file_data:
            self.assertEqual(blob.download_as_bytes(), _file_data.read())
        # We don't know the current version of the key.
        self.assertTrue(blob.kms_key_name.startswith(kms_key_name))

        (listed,) = list(Config.CLIENT.list_blobs(self.bucket))
        self.assertTrue(listed.kms_key_name.startswith(kms_key_name))

    @RetryErrors(unittest.TestCase.failureException)
    def test_bucket_w_default_kms_key_name(self):
        BLOB_NAME = "default-kms-key-name"
        OVERRIDE_BLOB_NAME = "override-default-kms-key-name"
        ALT_BLOB_NAME = "alt-default-kms-key-name"
        CLEARTEXT_BLOB_NAME = "cleartext"

        file_data = self.FILES["simple"]

        with open(file_data["path"], "rb") as _file_data:
            contents = _file_data.read()

        kms_key_name = self._kms_key_name()
        self.bucket.default_kms_key_name = kms_key_name
        self.bucket.patch()
        self.assertEqual(self.bucket.default_kms_key_name, kms_key_name)

        defaulted_blob = self.bucket.blob(BLOB_NAME)
        defaulted_blob.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(defaulted_blob)

        self.assertEqual(defaulted_blob.download_as_bytes(), contents)
        # We don't know the current version of the key.
        self.assertTrue(defaulted_blob.kms_key_name.startswith(kms_key_name))

        alt_kms_key_name = self._kms_key_name(self.ALT_KEY_NAME)

        override_blob = self.bucket.blob(
            OVERRIDE_BLOB_NAME, kms_key_name=alt_kms_key_name
        )
        override_blob.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(override_blob)

        self.assertEqual(override_blob.download_as_bytes(), contents)
        # We don't know the current version of the key.
        self.assertTrue(override_blob.kms_key_name.startswith(alt_kms_key_name))

        self.bucket.default_kms_key_name = alt_kms_key_name
        self.bucket.patch()

        alt_blob = self.bucket.blob(ALT_BLOB_NAME)
        alt_blob.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(alt_blob)

        self.assertEqual(alt_blob.download_as_bytes(), contents)
        # We don't know the current version of the key.
        self.assertTrue(alt_blob.kms_key_name.startswith(alt_kms_key_name))

        self.bucket.default_kms_key_name = None
        self.bucket.patch()

        cleartext_blob = self.bucket.blob(CLEARTEXT_BLOB_NAME)
        cleartext_blob.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(cleartext_blob)

        self.assertEqual(cleartext_blob.download_as_bytes(), contents)
        self.assertIsNone(cleartext_blob.kms_key_name)

    def test_rewrite_rotate_csek_to_cmek(self):
        BLOB_NAME = "rotating-keys"
        file_data = self.FILES["simple"]

        SOURCE_KEY = os.urandom(32)
        source = self.bucket.blob(BLOB_NAME, encryption_key=SOURCE_KEY)
        source.upload_from_filename(file_data["path"])
        self.case_blobs_to_delete.append(source)
        source_data = source.download_as_bytes()

        kms_key_name = self._kms_key_name()

        # We can't verify it, but ideally we would check that the following
        # URL was resolvable with our credentials
        # KEY_URL = 'https://cloudkms.googleapis.com/v1/{}'.format(
        #     kms_key_name)

        dest = self.bucket.blob(BLOB_NAME, kms_key_name=kms_key_name)
        token, rewritten, total = dest.rewrite(source)

        while token is not None:
            token, rewritten, total = dest.rewrite(source, token=token)

        # Not adding 'dest' to 'self.case_blobs_to_delete':  it is the
        # same object as 'source'.

        self.assertIsNone(token)
        self.assertEqual(rewritten, len(source_data))
        self.assertEqual(total, len(source_data))

        self.assertEqual(dest.download_as_bytes(), source_data)

    def test_upload_new_blob_w_bucket_cmek_enabled(self):
        blob_name = "test-blob"
        payload = b"DEADBEEF"
        alt_payload = b"NEWDEADBEEF"

        kms_key_name = self._kms_key_name()
        self.bucket.default_kms_key_name = kms_key_name
        self.bucket.patch()
        self.assertEqual(self.bucket.default_kms_key_name, kms_key_name)

        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(payload)
        retry_429_harder(blob.reload)()
        # We don't know the current version of the key.
        self.assertTrue(blob.kms_key_name.startswith(kms_key_name))

        blob.upload_from_string(alt_payload, if_generation_match=blob.generation)
        self.case_blobs_to_delete.append(blob)

        self.assertEqual(blob.download_as_bytes(), alt_payload)

        self.bucket.default_kms_key_name = None
        retry_429_harder(self.bucket.patch)()
        self.assertIsNone(self.bucket.default_kms_key_name)


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
