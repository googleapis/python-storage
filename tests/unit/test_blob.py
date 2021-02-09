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

import base64
import datetime
import hashlib
import io
import json
import os
import tempfile
import unittest

import mock
import pytest
import six
from six.moves import http_client

from google.cloud.storage.retry import DEFAULT_RETRY
from google.cloud.storage.retry import DEFAULT_RETRY_IF_GENERATION_SPECIFIED


def _make_credentials():
    import google.auth.credentials

    return mock.Mock(spec=google.auth.credentials.Credentials)


class Test_Blob(unittest.TestCase):
    @staticmethod
    def _make_one(*args, **kw):
        from google.cloud.storage.blob import Blob

        properties = kw.pop("properties", {})
        blob = Blob(*args, **kw)
        blob._properties.update(properties)
        return blob

    @staticmethod
    def _get_default_timeout():
        from google.cloud.storage.constants import _DEFAULT_TIMEOUT

        return _DEFAULT_TIMEOUT

    @staticmethod
    def _make_client(*args, **kw):
        from google.cloud.storage.client import Client

        return Client(*args, **kw)

    def test_ctor_wo_encryption_key(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        properties = {"key": "value"}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertIs(blob.bucket, bucket)
        self.assertEqual(blob.name, BLOB_NAME)
        self.assertEqual(blob._properties, properties)
        self.assertFalse(blob._acl.loaded)
        self.assertIs(blob._acl.blob, blob)
        self.assertEqual(blob._encryption_key, None)
        self.assertEqual(blob.kms_key_name, None)

    def test_ctor_with_encoded_unicode(self):
        blob_name = b"wet \xe2\x9b\xb5"
        blob = self._make_one(blob_name, bucket=None)
        unicode_name = u"wet \N{sailboat}"
        self.assertNotIsInstance(blob.name, bytes)
        self.assertIsInstance(blob.name, six.text_type)
        self.assertEqual(blob.name, unicode_name)

    def test_ctor_w_encryption_key(self):
        KEY = b"01234567890123456789012345678901"  # 32 bytes
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket, encryption_key=KEY)
        self.assertEqual(blob._encryption_key, KEY)
        self.assertEqual(blob.kms_key_name, None)

    def test_ctor_w_kms_key_name_and_encryption_key(self):
        KEY = b"01234567890123456789012345678901"  # 32 bytes
        KMS_RESOURCE = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
        )
        BLOB_NAME = "blob-name"
        bucket = _Bucket()

        with self.assertRaises(ValueError):
            self._make_one(
                BLOB_NAME, bucket=bucket, encryption_key=KEY, kms_key_name=KMS_RESOURCE
            )

    def test_ctor_w_kms_key_name(self):
        KMS_RESOURCE = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
        )
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket, kms_key_name=KMS_RESOURCE)
        self.assertEqual(blob._encryption_key, None)
        self.assertEqual(blob.kms_key_name, KMS_RESOURCE)

    def test_ctor_with_generation(self):
        BLOB_NAME = "blob-name"
        GENERATION = 12345
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket, generation=GENERATION)
        self.assertEqual(blob.generation, GENERATION)

    def _set_properties_helper(self, kms_key_name=None):
        import datetime
        from google.cloud._helpers import UTC
        from google.cloud._helpers import _RFC3339_MICROS

        now = datetime.datetime.utcnow().replace(tzinfo=UTC)
        NOW = now.strftime(_RFC3339_MICROS)
        BLOB_NAME = "blob-name"
        GENERATION = 12345
        BLOB_ID = "name/{}/{}".format(BLOB_NAME, GENERATION)
        SELF_LINK = "http://example.com/self/"
        METAGENERATION = 23456
        SIZE = 12345
        MD5_HASH = "DEADBEEF"
        MEDIA_LINK = "http://example.com/media/"
        ENTITY = "project-owner-12345"
        ENTITY_ID = "23456"
        CRC32C = "FACE0DAC"
        COMPONENT_COUNT = 2
        ETAG = "ETAG"
        resource = {
            "id": BLOB_ID,
            "selfLink": SELF_LINK,
            "generation": GENERATION,
            "metageneration": METAGENERATION,
            "contentType": "text/plain",
            "timeCreated": NOW,
            "updated": NOW,
            "timeDeleted": NOW,
            "storageClass": "NEARLINE",
            "timeStorageClassUpdated": NOW,
            "size": SIZE,
            "md5Hash": MD5_HASH,
            "mediaLink": MEDIA_LINK,
            "contentEncoding": "gzip",
            "contentDisposition": "inline",
            "contentLanguage": "en-US",
            "cacheControl": "private",
            "metadata": {"foo": "Foo"},
            "owner": {"entity": ENTITY, "entityId": ENTITY_ID},
            "crc32c": CRC32C,
            "componentCount": COMPONENT_COUNT,
            "etag": ETAG,
            "customTime": NOW,
        }

        if kms_key_name is not None:
            resource["kmsKeyName"] = kms_key_name

        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        blob._set_properties(resource)

        self.assertEqual(blob.id, BLOB_ID)
        self.assertEqual(blob.self_link, SELF_LINK)
        self.assertEqual(blob.generation, GENERATION)
        self.assertEqual(blob.metageneration, METAGENERATION)
        self.assertEqual(blob.content_type, "text/plain")
        self.assertEqual(blob.time_created, now)
        self.assertEqual(blob.updated, now)
        self.assertEqual(blob.time_deleted, now)
        self.assertEqual(blob.storage_class, "NEARLINE")
        self.assertEqual(blob.size, SIZE)
        self.assertEqual(blob.md5_hash, MD5_HASH)
        self.assertEqual(blob.media_link, MEDIA_LINK)
        self.assertEqual(blob.content_encoding, "gzip")
        self.assertEqual(blob.content_disposition, "inline")
        self.assertEqual(blob.content_language, "en-US")
        self.assertEqual(blob.cache_control, "private")
        self.assertEqual(blob.metadata, {"foo": "Foo"})
        self.assertEqual(blob.owner, {"entity": ENTITY, "entityId": ENTITY_ID})
        self.assertEqual(blob.crc32c, CRC32C)
        self.assertEqual(blob.component_count, COMPONENT_COUNT)
        self.assertEqual(blob.etag, ETAG)
        self.assertEqual(blob.custom_time, now)

        if kms_key_name is not None:
            self.assertEqual(blob.kms_key_name, kms_key_name)
        else:
            self.assertIsNone(blob.kms_key_name)

    def test__set_properties_wo_kms_key_name(self):
        self._set_properties_helper()

    def test__set_properties_w_kms_key_name(self):
        kms_resource = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
        )
        self._set_properties_helper(kms_key_name=kms_resource)

    def test_chunk_size_ctor(self):
        from google.cloud.storage.blob import Blob

        BLOB_NAME = "blob-name"
        BUCKET = object()
        chunk_size = 10 * Blob._CHUNK_SIZE_MULTIPLE
        blob = self._make_one(BLOB_NAME, bucket=BUCKET, chunk_size=chunk_size)
        self.assertEqual(blob._chunk_size, chunk_size)

    def test_chunk_size_getter(self):
        BLOB_NAME = "blob-name"
        BUCKET = object()
        blob = self._make_one(BLOB_NAME, bucket=BUCKET)
        self.assertIsNone(blob.chunk_size)
        VALUE = object()
        blob._chunk_size = VALUE
        self.assertIs(blob.chunk_size, VALUE)

    def test_chunk_size_setter(self):
        BLOB_NAME = "blob-name"
        BUCKET = object()
        blob = self._make_one(BLOB_NAME, bucket=BUCKET)
        self.assertIsNone(blob._chunk_size)
        blob._CHUNK_SIZE_MULTIPLE = 10
        blob.chunk_size = 20
        self.assertEqual(blob._chunk_size, 20)

    def test_chunk_size_setter_bad_value(self):
        BLOB_NAME = "blob-name"
        BUCKET = object()
        blob = self._make_one(BLOB_NAME, bucket=BUCKET)
        self.assertIsNone(blob._chunk_size)
        blob._CHUNK_SIZE_MULTIPLE = 10
        with self.assertRaises(ValueError):
            blob.chunk_size = 11

    def test_acl_property(self):
        from google.cloud.storage.acl import ObjectACL

        fake_bucket = _Bucket()
        blob = self._make_one(u"name", bucket=fake_bucket)
        acl = blob.acl
        self.assertIsInstance(acl, ObjectACL)
        self.assertIs(acl, blob._acl)

    def test_path_bad_bucket(self):
        fake_bucket = object()
        name = u"blob-name"
        blob = self._make_one(name, bucket=fake_bucket)
        self.assertRaises(AttributeError, getattr, blob, "path")

    def test_path_no_name(self):
        bucket = _Bucket()
        blob = self._make_one(u"", bucket=bucket)
        self.assertRaises(ValueError, getattr, blob, "path")

    def test_path_normal(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertEqual(blob.path, "/b/name/o/%s" % BLOB_NAME)

    def test_path_w_slash_in_name(self):
        BLOB_NAME = "parent/child"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertEqual(blob.path, "/b/name/o/parent%2Fchild")

    def test_path_with_non_ascii(self):
        blob_name = u"Caf\xe9"
        bucket = _Bucket()
        blob = self._make_one(blob_name, bucket=bucket)
        self.assertEqual(blob.path, "/b/name/o/Caf%C3%A9")

    def test_bucket_readonly_property(self):
        blob_name = "BLOB"
        bucket = _Bucket()
        other = _Bucket()
        blob = self._make_one(blob_name, bucket=bucket)
        with self.assertRaises(AttributeError):
            blob.bucket = other

    def test_client(self):
        blob_name = "BLOB"
        bucket = _Bucket()
        blob = self._make_one(blob_name, bucket=bucket)
        self.assertIs(blob.client, bucket.client)

    def test_user_project(self):
        user_project = "user-project-123"
        blob_name = "BLOB"
        bucket = _Bucket(user_project=user_project)
        blob = self._make_one(blob_name, bucket=bucket)
        self.assertEqual(blob.user_project, user_project)

    def test__encryption_headers_wo_encryption_key(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        expected = {}
        self.assertEqual(blob._encryption_headers(), expected)

    def test__encryption_headers_w_encryption_key(self):
        key = b"aa426195405adee2c8081bb9e7e74b19"
        header_key_value = "YWE0MjYxOTU0MDVhZGVlMmM4MDgxYmI5ZTdlNzRiMTk="
        header_key_hash_value = "V3Kwe46nKc3xLv96+iJ707YfZfFvlObta8TQcx2gpm0="
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket, encryption_key=key)
        expected = {
            "X-Goog-Encryption-Algorithm": "AES256",
            "X-Goog-Encryption-Key": header_key_value,
            "X-Goog-Encryption-Key-Sha256": header_key_hash_value,
        }
        self.assertEqual(blob._encryption_headers(), expected)

    def test__query_params_default(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertEqual(blob._query_params, {})

    def test__query_params_w_user_project(self):
        user_project = "user-project-123"
        BLOB_NAME = "BLOB"
        bucket = _Bucket(user_project=user_project)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertEqual(blob._query_params, {"userProject": user_project})

    def test__query_params_w_generation(self):
        generation = 123456
        BLOB_NAME = "BLOB"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket, generation=generation)
        self.assertEqual(blob._query_params, {"generation": generation})

    def test_public_url(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertEqual(
            blob.public_url, "https://storage.googleapis.com/name/%s" % BLOB_NAME
        )

    def test_public_url_w_slash_in_name(self):
        BLOB_NAME = "parent/child"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertEqual(
            blob.public_url, "https://storage.googleapis.com/name/parent/child"
        )

    def test_public_url_w_tilde_in_name(self):
        BLOB_NAME = "foo~bar"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertEqual(blob.public_url, "https://storage.googleapis.com/name/foo~bar")

    def test_public_url_with_non_ascii(self):
        blob_name = u"winter \N{snowman}"
        bucket = _Bucket()
        blob = self._make_one(blob_name, bucket=bucket)
        expected_url = "https://storage.googleapis.com/name/winter%20%E2%98%83"
        self.assertEqual(blob.public_url, expected_url)

    def test_generate_signed_url_w_invalid_version(self):
        BLOB_NAME = "blob-name"
        EXPIRATION = "2014-10-16T20:34:37.000Z"
        connection = _Connection()
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        with self.assertRaises(ValueError):
            blob.generate_signed_url(EXPIRATION, version="nonesuch")

    def _generate_signed_url_helper(
        self,
        version=None,
        blob_name="blob-name",
        api_access_endpoint=None,
        method="GET",
        content_md5=None,
        content_type=None,
        response_type=None,
        response_disposition=None,
        generation=None,
        headers=None,
        query_parameters=None,
        credentials=None,
        expiration=None,
        encryption_key=None,
        access_token=None,
        service_account_email=None,
        virtual_hosted_style=False,
        bucket_bound_hostname=None,
        scheme="http",
    ):
        from six.moves.urllib import parse
        from google.cloud._helpers import UTC
        from google.cloud.storage._helpers import _bucket_bound_hostname_url
        from google.cloud.storage.blob import _API_ACCESS_ENDPOINT
        from google.cloud.storage.blob import _get_encryption_headers

        api_access_endpoint = api_access_endpoint or _API_ACCESS_ENDPOINT

        delta = datetime.timedelta(hours=1)

        if expiration is None:
            expiration = datetime.datetime.utcnow().replace(tzinfo=UTC) + delta

        connection = _Connection()
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(blob_name, bucket=bucket, encryption_key=encryption_key)

        if version is None:
            effective_version = "v2"
        else:
            effective_version = version

        to_patch = "google.cloud.storage.blob.generate_signed_url_{}".format(
            effective_version
        )

        with mock.patch(to_patch) as signer:
            signed_uri = blob.generate_signed_url(
                expiration=expiration,
                api_access_endpoint=api_access_endpoint,
                method=method,
                credentials=credentials,
                content_md5=content_md5,
                content_type=content_type,
                response_type=response_type,
                response_disposition=response_disposition,
                generation=generation,
                headers=headers,
                query_parameters=query_parameters,
                version=version,
                access_token=access_token,
                service_account_email=service_account_email,
                virtual_hosted_style=virtual_hosted_style,
                bucket_bound_hostname=bucket_bound_hostname,
            )

        self.assertEqual(signed_uri, signer.return_value)

        if credentials is None:
            expected_creds = _Connection.credentials
        else:
            expected_creds = credentials

        encoded_name = blob_name.encode("utf-8")
        quoted_name = parse.quote(encoded_name, safe=b"/~")

        if virtual_hosted_style:
            expected_api_access_endpoint = "https://{}.storage.googleapis.com".format(
                bucket.name
            )
        elif bucket_bound_hostname:
            expected_api_access_endpoint = _bucket_bound_hostname_url(
                bucket_bound_hostname, scheme
            )
        else:
            expected_api_access_endpoint = api_access_endpoint
            expected_resource = "/{}/{}".format(bucket.name, quoted_name)

        if virtual_hosted_style or bucket_bound_hostname:
            expected_resource = "/{}".format(quoted_name)

        if encryption_key is not None:
            expected_headers = headers or {}
            if effective_version == "v2":
                expected_headers["X-Goog-Encryption-Algorithm"] = "AES256"
            else:
                expected_headers.update(_get_encryption_headers(encryption_key))
        else:
            expected_headers = headers

        expected_kwargs = {
            "resource": expected_resource,
            "expiration": expiration,
            "api_access_endpoint": expected_api_access_endpoint,
            "method": method.upper(),
            "content_md5": content_md5,
            "content_type": content_type,
            "response_type": response_type,
            "response_disposition": response_disposition,
            "generation": generation,
            "headers": expected_headers,
            "query_parameters": query_parameters,
            "access_token": access_token,
            "service_account_email": service_account_email,
        }
        signer.assert_called_once_with(expected_creds, **expected_kwargs)

    def test_generate_signed_url_no_version_passed_warning(self):
        self._generate_signed_url_helper()

    def _generate_signed_url_v2_helper(self, **kw):
        version = "v2"
        self._generate_signed_url_helper(version, **kw)

    def test_generate_signed_url_v2_w_defaults(self):
        self._generate_signed_url_v2_helper()

    def test_generate_signed_url_v2_w_expiration(self):
        from google.cloud._helpers import UTC

        expiration = datetime.datetime.utcnow().replace(tzinfo=UTC)
        self._generate_signed_url_v2_helper(expiration=expiration)

    def test_generate_signed_url_v2_w_non_ascii_name(self):
        BLOB_NAME = u"\u0410\u043a\u043a\u043e\u0440\u0434\u044b.txt"
        self._generate_signed_url_v2_helper(blob_name=BLOB_NAME)

    def test_generate_signed_url_v2_w_slash_in_name(self):
        BLOB_NAME = "parent/child"
        self._generate_signed_url_v2_helper(blob_name=BLOB_NAME)

    def test_generate_signed_url_v2_w_tilde_in_name(self):
        BLOB_NAME = "foo~bar"
        self._generate_signed_url_v2_helper(blob_name=BLOB_NAME)

    def test_generate_signed_url_v2_w_endpoint(self):
        self._generate_signed_url_v2_helper(
            api_access_endpoint="https://api.example.com/v1"
        )

    def test_generate_signed_url_v2_w_method(self):
        self._generate_signed_url_v2_helper(method="POST")

    def test_generate_signed_url_v2_w_lowercase_method(self):
        self._generate_signed_url_v2_helper(method="get")

    def test_generate_signed_url_v2_w_content_md5(self):
        self._generate_signed_url_v2_helper(content_md5="FACEDACE")

    def test_generate_signed_url_v2_w_content_type(self):
        self._generate_signed_url_v2_helper(content_type="text.html")

    def test_generate_signed_url_v2_w_response_type(self):
        self._generate_signed_url_v2_helper(response_type="text.html")

    def test_generate_signed_url_v2_w_response_disposition(self):
        self._generate_signed_url_v2_helper(response_disposition="inline")

    def test_generate_signed_url_v2_w_generation(self):
        self._generate_signed_url_v2_helper(generation=12345)

    def test_generate_signed_url_v2_w_headers(self):
        self._generate_signed_url_v2_helper(headers={"x-goog-foo": "bar"})

    def test_generate_signed_url_v2_w_csek(self):
        self._generate_signed_url_v2_helper(encryption_key=os.urandom(32))

    def test_generate_signed_url_v2_w_csek_and_headers(self):
        self._generate_signed_url_v2_helper(
            encryption_key=os.urandom(32), headers={"x-goog-foo": "bar"}
        )

    def test_generate_signed_url_v2_w_credentials(self):
        credentials = object()
        self._generate_signed_url_v2_helper(credentials=credentials)

    def _generate_signed_url_v4_helper(self, **kw):
        version = "v4"
        self._generate_signed_url_helper(version, **kw)

    def test_generate_signed_url_v4_w_defaults(self):
        self._generate_signed_url_v4_helper()

    def test_generate_signed_url_v4_w_non_ascii_name(self):
        BLOB_NAME = u"\u0410\u043a\u043a\u043e\u0440\u0434\u044b.txt"
        self._generate_signed_url_v4_helper(blob_name=BLOB_NAME)

    def test_generate_signed_url_v4_w_slash_in_name(self):
        BLOB_NAME = "parent/child"
        self._generate_signed_url_v4_helper(blob_name=BLOB_NAME)

    def test_generate_signed_url_v4_w_tilde_in_name(self):
        BLOB_NAME = "foo~bar"
        self._generate_signed_url_v4_helper(blob_name=BLOB_NAME)

    def test_generate_signed_url_v4_w_endpoint(self):
        self._generate_signed_url_v4_helper(
            api_access_endpoint="https://api.example.com/v1"
        )

    def test_generate_signed_url_v4_w_method(self):
        self._generate_signed_url_v4_helper(method="POST")

    def test_generate_signed_url_v4_w_lowercase_method(self):
        self._generate_signed_url_v4_helper(method="get")

    def test_generate_signed_url_v4_w_content_md5(self):
        self._generate_signed_url_v4_helper(content_md5="FACEDACE")

    def test_generate_signed_url_v4_w_content_type(self):
        self._generate_signed_url_v4_helper(content_type="text.html")

    def test_generate_signed_url_v4_w_response_type(self):
        self._generate_signed_url_v4_helper(response_type="text.html")

    def test_generate_signed_url_v4_w_response_disposition(self):
        self._generate_signed_url_v4_helper(response_disposition="inline")

    def test_generate_signed_url_v4_w_generation(self):
        self._generate_signed_url_v4_helper(generation=12345)

    def test_generate_signed_url_v4_w_headers(self):
        self._generate_signed_url_v4_helper(headers={"x-goog-foo": "bar"})

    def test_generate_signed_url_v4_w_csek(self):
        self._generate_signed_url_v4_helper(encryption_key=os.urandom(32))

    def test_generate_signed_url_v4_w_csek_and_headers(self):
        self._generate_signed_url_v4_helper(
            encryption_key=os.urandom(32), headers={"x-goog-foo": "bar"}
        )

    def test_generate_signed_url_v4_w_virtual_hostname(self):
        self._generate_signed_url_v4_helper(virtual_hosted_style=True)

    def test_generate_signed_url_v4_w_bucket_bound_hostname_w_scheme(self):
        self._generate_signed_url_v4_helper(
            bucket_bound_hostname="http://cdn.example.com"
        )

    def test_generate_signed_url_v4_w_bucket_bound_hostname_w_bare_hostname(self):
        self._generate_signed_url_v4_helper(bucket_bound_hostname="cdn.example.com")

    def test_generate_signed_url_v4_w_credentials(self):
        credentials = object()
        self._generate_signed_url_v4_helper(credentials=credentials)

    def test_exists_miss(self):
        NONESUCH = "nonesuch"
        not_found_response = ({"status": http_client.NOT_FOUND}, b"")
        connection = _Connection(not_found_response)
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(NONESUCH, bucket=bucket)
        self.assertFalse(blob.exists(timeout=42))
        self.assertEqual(len(connection._requested), 1)
        self.assertEqual(
            connection._requested[0],
            {
                "method": "GET",
                "path": "/b/name/o/{}".format(NONESUCH),
                "query_params": {"fields": "name"},
                "_target_object": None,
                "timeout": 42,
                "retry": DEFAULT_RETRY,
            },
        )

    def test_exists_hit_w_user_project(self):
        BLOB_NAME = "blob-name"
        USER_PROJECT = "user-project-123"
        found_response = ({"status": http_client.OK}, b"")
        connection = _Connection(found_response)
        client = _Client(connection)
        bucket = _Bucket(client, user_project=USER_PROJECT)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        bucket._blobs[BLOB_NAME] = 1
        self.assertTrue(blob.exists())
        self.assertEqual(len(connection._requested), 1)
        self.assertEqual(
            connection._requested[0],
            {
                "method": "GET",
                "path": "/b/name/o/{}".format(BLOB_NAME),
                "query_params": {"fields": "name", "userProject": USER_PROJECT},
                "_target_object": None,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY,
            },
        )

    def test_exists_hit_w_generation(self):
        BLOB_NAME = "blob-name"
        GENERATION = 123456
        found_response = ({"status": http_client.OK}, b"")
        connection = _Connection(found_response)
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(BLOB_NAME, bucket=bucket, generation=GENERATION)
        bucket._blobs[BLOB_NAME] = 1
        self.assertTrue(blob.exists())
        self.assertEqual(len(connection._requested), 1)
        self.assertEqual(
            connection._requested[0],
            {
                "method": "GET",
                "path": "/b/name/o/{}".format(BLOB_NAME),
                "query_params": {"fields": "name", "generation": GENERATION},
                "_target_object": None,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY,
            },
        )

    def test_exists_w_generation_match(self):
        BLOB_NAME = "blob-name"
        GENERATION_NUMBER = 123456
        METAGENERATION_NUMBER = 6

        found_response = ({"status": http_client.OK}, b"")
        connection = _Connection(found_response)
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        bucket._blobs[BLOB_NAME] = 1
        self.assertTrue(
            blob.exists(
                if_generation_match=GENERATION_NUMBER,
                if_metageneration_match=METAGENERATION_NUMBER,
            )
        )
        self.assertEqual(len(connection._requested), 1)
        self.assertEqual(
            connection._requested[0],
            {
                "method": "GET",
                "path": "/b/name/o/{}".format(BLOB_NAME),
                "query_params": {
                    "fields": "name",
                    "ifGenerationMatch": GENERATION_NUMBER,
                    "ifMetagenerationMatch": METAGENERATION_NUMBER,
                },
                "_target_object": None,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY,
            },
        )

    def test_delete_wo_generation(self):
        BLOB_NAME = "blob-name"
        not_found_response = ({"status": http_client.NOT_FOUND}, b"")
        connection = _Connection(not_found_response)
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        bucket._blobs[BLOB_NAME] = 1
        blob.delete()
        self.assertFalse(blob.exists())
        self.assertEqual(
            bucket._deleted,
            [
                (
                    BLOB_NAME,
                    None,
                    None,
                    self._get_default_timeout(),
                    None,
                    None,
                    None,
                    None,
                    DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
                )
            ],
        )

    def test_delete_w_generation(self):
        BLOB_NAME = "blob-name"
        GENERATION = 123456
        not_found_response = ({"status": http_client.NOT_FOUND}, b"")
        connection = _Connection(not_found_response)
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(BLOB_NAME, bucket=bucket, generation=GENERATION)
        bucket._blobs[BLOB_NAME] = 1
        blob.delete(timeout=42)
        self.assertFalse(blob.exists())
        self.assertEqual(
            bucket._deleted,
            [
                (
                    BLOB_NAME,
                    None,
                    GENERATION,
                    42,
                    None,
                    None,
                    None,
                    None,
                    DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
                )
            ],
        )

    def test_delete_w_generation_match(self):
        BLOB_NAME = "blob-name"
        GENERATION = 123456
        not_found_response = ({"status": http_client.NOT_FOUND}, b"")
        connection = _Connection(not_found_response)
        client = _Client(connection)
        bucket = _Bucket(client)
        blob = self._make_one(BLOB_NAME, bucket=bucket, generation=GENERATION)
        bucket._blobs[BLOB_NAME] = 1
        blob.delete(timeout=42, if_generation_match=GENERATION)
        self.assertFalse(blob.exists())
        self.assertEqual(
            bucket._deleted,
            [
                (
                    BLOB_NAME,
                    None,
                    GENERATION,
                    42,
                    GENERATION,
                    None,
                    None,
                    None,
                    DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
                )
            ],
        )

    def test__get_transport(self):
        client = mock.Mock(spec=[u"_credentials", "_http"])
        client._http = mock.sentinel.transport
        blob = self._make_one(u"blob-name", bucket=None)

        transport = blob._get_transport(client)

        self.assertIs(transport, mock.sentinel.transport)

    def test__get_download_url_with_media_link(self):
        blob_name = "something.txt"
        bucket = _Bucket(name="IRRELEVANT")
        blob = self._make_one(blob_name, bucket=bucket)
        media_link = "http://test.invalid"
        # Set the media link on the blob
        blob._properties["mediaLink"] = media_link

        client = mock.Mock(_connection=_Connection)
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        download_url = blob._get_download_url(client)

        self.assertEqual(download_url, media_link)

    def test__get_download_url_with_generation_match(self):
        GENERATION_NUMBER = 6
        MEDIA_LINK = "http://test.invalid"

        blob = self._make_one("something.txt", bucket=_Bucket(name="IRRELEVANT"))
        # Set the media link on the blob
        blob._properties["mediaLink"] = MEDIA_LINK

        client = mock.Mock(_connection=_Connection)
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        download_url = blob._get_download_url(
            client, if_generation_match=GENERATION_NUMBER
        )
        self.assertEqual(
            download_url,
            "{}?ifGenerationMatch={}".format(MEDIA_LINK, GENERATION_NUMBER),
        )

    def test__get_download_url_with_media_link_w_user_project(self):
        blob_name = "something.txt"
        user_project = "user-project-123"
        bucket = _Bucket(name="IRRELEVANT", user_project=user_project)
        blob = self._make_one(blob_name, bucket=bucket)
        media_link = "http://test.invalid"
        # Set the media link on the blob
        blob._properties["mediaLink"] = media_link

        client = mock.Mock(_connection=_Connection)
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        download_url = blob._get_download_url(client)

        self.assertEqual(
            download_url, "{}?userProject={}".format(media_link, user_project)
        )

    def test__get_download_url_on_the_fly(self):
        blob_name = "bzzz-fly.txt"
        bucket = _Bucket(name="buhkit")
        blob = self._make_one(blob_name, bucket=bucket)

        self.assertIsNone(blob.media_link)
        client = mock.Mock(_connection=_Connection)
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        download_url = blob._get_download_url(client)
        expected_url = (
            "https://storage.googleapis.com/download/storage/v1/b/"
            "buhkit/o/bzzz-fly.txt?alt=media"
        )
        self.assertEqual(download_url, expected_url)

    def test__get_download_url_on_the_fly_with_generation(self):
        blob_name = "pretend.txt"
        bucket = _Bucket(name="fictional")
        blob = self._make_one(blob_name, bucket=bucket)
        generation = 1493058489532987
        # Set the media link on the blob
        blob._properties["generation"] = str(generation)

        self.assertIsNone(blob.media_link)
        client = mock.Mock(_connection=_Connection)
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        download_url = blob._get_download_url(client)
        expected_url = (
            "https://storage.googleapis.com/download/storage/v1/b/"
            "fictional/o/pretend.txt?alt=media&generation=1493058489532987"
        )
        self.assertEqual(download_url, expected_url)

    def test__get_download_url_on_the_fly_with_user_project(self):
        blob_name = "pretend.txt"
        user_project = "user-project-123"
        bucket = _Bucket(name="fictional", user_project=user_project)
        blob = self._make_one(blob_name, bucket=bucket)

        self.assertIsNone(blob.media_link)
        client = mock.Mock(_connection=_Connection)
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        download_url = blob._get_download_url(client)
        expected_url = (
            "https://storage.googleapis.com/download/storage/v1/b/"
            "fictional/o/pretend.txt?alt=media&userProject={}".format(user_project)
        )
        self.assertEqual(download_url, expected_url)

    def test__get_download_url_on_the_fly_with_kms_key_name(self):
        kms_resource = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
        )
        blob_name = "bzzz-fly.txt"
        bucket = _Bucket(name="buhkit")
        blob = self._make_one(blob_name, bucket=bucket, kms_key_name=kms_resource)

        self.assertIsNone(blob.media_link)
        client = mock.Mock(_connection=_Connection)
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        download_url = blob._get_download_url(client)
        expected_url = (
            "https://storage.googleapis.com/download/storage/v1/b/"
            "buhkit/o/bzzz-fly.txt?alt=media"
        )
        self.assertEqual(download_url, expected_url)

    @staticmethod
    def _mock_requests_response(status_code, headers, content=b""):
        import requests

        response = requests.Response()
        response.status_code = status_code
        response.headers.update(headers)
        response.raw = None
        response._content = content

        response.request = requests.Request("POST", "http://example.com").prepare()
        return response

    def _do_download_helper_wo_chunks(self, w_range, raw_download, timeout=None):
        blob_name = "blob-name"
        client = mock.Mock()
        bucket = _Bucket(client)
        blob = self._make_one(blob_name, bucket=bucket)
        self.assertIsNone(blob.chunk_size)

        transport = object()
        file_obj = io.BytesIO()
        download_url = "http://test.invalid"
        headers = {}

        if raw_download:
            patch = mock.patch("google.cloud.storage.blob.RawDownload")
        else:
            patch = mock.patch("google.cloud.storage.blob.Download")

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        with patch as patched:
            if w_range:
                blob._do_download(
                    transport,
                    file_obj,
                    download_url,
                    headers,
                    start=1,
                    end=3,
                    raw_download=raw_download,
                    **timeout_kwarg
                )
            else:
                blob._do_download(
                    transport,
                    file_obj,
                    download_url,
                    headers,
                    raw_download=raw_download,
                    **timeout_kwarg
                )

        if w_range:
            patched.assert_called_once_with(
                download_url,
                stream=file_obj,
                headers=headers,
                start=1,
                end=3,
                checksum="md5",
            )
        else:
            patched.assert_called_once_with(
                download_url,
                stream=file_obj,
                headers=headers,
                start=None,
                end=None,
                checksum="md5",
            )

        patched.return_value.consume.assert_called_once_with(
            transport, timeout=expected_timeout
        )

    def test__do_download_wo_chunks_wo_range_wo_raw(self):
        self._do_download_helper_wo_chunks(w_range=False, raw_download=False)

    def test__do_download_wo_chunks_w_range_wo_raw(self):
        self._do_download_helper_wo_chunks(w_range=True, raw_download=False)

    def test__do_download_wo_chunks_wo_range_w_raw(self):
        self._do_download_helper_wo_chunks(w_range=False, raw_download=True)

    def test__do_download_wo_chunks_w_range_w_raw(self):
        self._do_download_helper_wo_chunks(w_range=True, raw_download=True)

    def test__do_download_wo_chunks_w_custom_timeout(self):
        self._do_download_helper_wo_chunks(
            w_range=False, raw_download=False, timeout=9.58
        )

    def _do_download_helper_w_chunks(
        self, w_range, raw_download, timeout=None, checksum="md5"
    ):
        blob_name = "blob-name"
        client = mock.Mock(_credentials=_make_credentials(), spec=["_credentials"])
        bucket = _Bucket(client)
        blob = self._make_one(blob_name, bucket=bucket)
        blob._CHUNK_SIZE_MULTIPLE = 1
        chunk_size = blob.chunk_size = 3

        transport = object()
        file_obj = io.BytesIO()
        download_url = "http://test.invalid"
        headers = {}

        download = mock.Mock(finished=False, spec=["finished", "consume_next_chunk"])

        def side_effect(*args, **kwargs):
            download.finished = True

        download.consume_next_chunk.side_effect = side_effect

        if raw_download:
            patch = mock.patch("google.cloud.storage.blob.RawChunkedDownload")
        else:
            patch = mock.patch("google.cloud.storage.blob.ChunkedDownload")

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        with patch as patched:
            patched.return_value = download
            if w_range:
                blob._do_download(
                    transport,
                    file_obj,
                    download_url,
                    headers,
                    start=1,
                    end=3,
                    raw_download=raw_download,
                    checksum=checksum,
                    **timeout_kwarg
                )
            else:
                blob._do_download(
                    transport,
                    file_obj,
                    download_url,
                    headers,
                    raw_download=raw_download,
                    checksum=checksum,
                    **timeout_kwarg
                )

        if w_range:
            patched.assert_called_once_with(
                download_url, chunk_size, file_obj, headers=headers, start=1, end=3
            )
        else:
            patched.assert_called_once_with(
                download_url, chunk_size, file_obj, headers=headers, start=0, end=None
            )
        download.consume_next_chunk.assert_called_once_with(
            transport, timeout=expected_timeout
        )

    def test__do_download_w_chunks_wo_range_wo_raw(self):
        self._do_download_helper_w_chunks(w_range=False, raw_download=False)

    def test__do_download_w_chunks_w_range_wo_raw(self):
        self._do_download_helper_w_chunks(w_range=True, raw_download=False)

    def test__do_download_w_chunks_wo_range_w_raw(self):
        self._do_download_helper_w_chunks(w_range=False, raw_download=True)

    def test__do_download_w_chunks_w_range_w_raw(self):
        self._do_download_helper_w_chunks(w_range=True, raw_download=True)

    def test__do_download_w_chunks_w_custom_timeout(self):
        self._do_download_helper_w_chunks(w_range=True, raw_download=True, timeout=9.58)

    def test__do_download_w_chunks_w_checksum(self):
        from google.cloud.storage import blob as blob_module

        with mock.patch.object(blob_module._logger, "info") as patch:
            self._do_download_helper_w_chunks(
                w_range=False, raw_download=False, checksum="md5"
            )
        patch.assert_called_once_with(
            blob_module._CHUNKED_DOWNLOAD_CHECKSUM_MESSAGE.format("md5")
        )

    def test__do_download_w_chunks_wo_checksum(self):
        from google.cloud.storage import blob as blob_module

        with mock.patch.object(blob_module._logger, "info") as patch:
            self._do_download_helper_w_chunks(
                w_range=False, raw_download=False, checksum=None
            )
        patch.assert_not_called()

    def test_download_to_file_with_failure(self):
        import requests
        from google.resumable_media import InvalidResponse
        from google.cloud import exceptions

        raw_response = requests.Response()
        raw_response.status_code = http_client.NOT_FOUND
        raw_request = requests.Request("GET", "http://example.com")
        raw_response.request = raw_request.prepare()
        grmp_response = InvalidResponse(raw_response)

        blob_name = "blob-name"
        media_link = "http://test.invalid"
        client = self._make_client()
        bucket = _Bucket(client)
        blob = self._make_one(blob_name, bucket=bucket)
        blob._properties["mediaLink"] = media_link
        blob._do_download = mock.Mock()
        blob._do_download.side_effect = grmp_response

        file_obj = io.BytesIO()
        with self.assertRaises(exceptions.NotFound):
            blob.download_to_file(file_obj)

        self.assertEqual(file_obj.tell(), 0)

        headers = {"accept-encoding": "gzip"}
        blob._do_download.assert_called_once_with(
            client._http,
            file_obj,
            media_link,
            headers,
            None,
            None,
            False,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )

    def test_download_to_file_wo_media_link(self):
        blob_name = "blob-name"
        client = self._make_client()
        bucket = _Bucket(client)
        blob = self._make_one(blob_name, bucket=bucket)
        blob._do_download = mock.Mock()
        file_obj = io.BytesIO()

        blob.download_to_file(file_obj)

        # Make sure the media link is still unknown.
        self.assertIsNone(blob.media_link)

        expected_url = (
            "https://storage.googleapis.com/download/storage/v1/b/"
            "name/o/blob-name?alt=media"
        )
        headers = {"accept-encoding": "gzip"}
        blob._do_download.assert_called_once_with(
            client._http,
            file_obj,
            expected_url,
            headers,
            None,
            None,
            False,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )

    def test_download_to_file_w_generation_match(self):
        GENERATION_NUMBER = 6
        HEADERS = {"accept-encoding": "gzip"}
        EXPECTED_URL = (
            "https://storage.googleapis.com/download/storage/v1/b/"
            "name/o/blob-name?alt=media&ifGenerationNotMatch={}".format(
                GENERATION_NUMBER
            )
        )

        client = self._make_client()
        blob = self._make_one("blob-name", bucket=_Bucket(client))
        blob._do_download = mock.Mock()
        file_obj = io.BytesIO()

        blob.download_to_file(file_obj, if_generation_not_match=GENERATION_NUMBER)

        blob._do_download.assert_called_once_with(
            client._http,
            file_obj,
            EXPECTED_URL,
            HEADERS,
            None,
            None,
            False,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )

    def _download_to_file_helper(self, use_chunks, raw_download, timeout=None):
        blob_name = "blob-name"
        client = self._make_client()
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {"mediaLink": media_link}
        blob = self._make_one(blob_name, bucket=bucket, properties=properties)
        if use_chunks:
            blob._CHUNK_SIZE_MULTIPLE = 1
            blob.chunk_size = 3
        blob._do_download = mock.Mock()

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        file_obj = io.BytesIO()
        if raw_download:
            blob.download_to_file(file_obj, raw_download=True, **timeout_kwarg)
        else:
            blob.download_to_file(file_obj, **timeout_kwarg)

        headers = {"accept-encoding": "gzip"}
        blob._do_download.assert_called_once_with(
            client._http,
            file_obj,
            media_link,
            headers,
            None,
            None,
            raw_download,
            timeout=expected_timeout,
            checksum="md5",
        )

    def test_download_to_file_wo_chunks_wo_raw(self):
        self._download_to_file_helper(use_chunks=False, raw_download=False)

    def test_download_to_file_w_chunks_wo_raw(self):
        self._download_to_file_helper(use_chunks=True, raw_download=False)

    def test_download_to_file_wo_chunks_w_raw(self):
        self._download_to_file_helper(use_chunks=False, raw_download=True)

    def test_download_to_file_w_chunks_w_raw(self):
        self._download_to_file_helper(use_chunks=True, raw_download=True)

    def test_download_to_file_w_custom_timeout(self):
        self._download_to_file_helper(
            use_chunks=False, raw_download=False, timeout=9.58
        )

    def _download_to_filename_helper(self, updated, raw_download, timeout=None):
        import os
        from google.cloud.storage._helpers import _convert_to_timestamp
        from google.cloud._testing import _NamedTemporaryFile

        blob_name = "blob-name"
        client = self._make_client()
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {"mediaLink": media_link}
        if updated is not None:
            properties["updated"] = updated

        blob = self._make_one(blob_name, bucket=bucket, properties=properties)
        blob._do_download = mock.Mock()

        with _NamedTemporaryFile() as temp:
            if timeout is None:
                blob.download_to_filename(temp.name, raw_download=raw_download)
            else:
                blob.download_to_filename(
                    temp.name, raw_download=raw_download, timeout=timeout,
                )

            if updated is None:
                self.assertIsNone(blob.updated)
            else:
                mtime = os.path.getmtime(temp.name)
                if six.PY2:
                    updated_time = _convert_to_timestamp(blob.updated)
                else:
                    updated_time = blob.updated.timestamp()
                self.assertEqual(mtime, updated_time)

        expected_timeout = self._get_default_timeout() if timeout is None else timeout

        headers = {"accept-encoding": "gzip"}
        blob._do_download.assert_called_once_with(
            client._http,
            mock.ANY,
            media_link,
            headers,
            None,
            None,
            raw_download,
            timeout=expected_timeout,
            checksum="md5",
        )
        stream = blob._do_download.mock_calls[0].args[1]
        self.assertEqual(stream.name, temp.name)

    def test_download_to_filename_w_generation_match(self):
        from google.cloud._testing import _NamedTemporaryFile

        GENERATION_NUMBER = 6
        MEDIA_LINK = "http://example.com/media/"
        EXPECTED_LINK = MEDIA_LINK + "?ifGenerationMatch={}".format(GENERATION_NUMBER)
        HEADERS = {"accept-encoding": "gzip"}

        client = self._make_client()

        blob = self._make_one(
            "blob-name", bucket=_Bucket(client), properties={"mediaLink": MEDIA_LINK}
        )
        blob._do_download = mock.Mock()

        with _NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name, if_generation_match=GENERATION_NUMBER)

        blob._do_download.assert_called_once_with(
            client._http,
            mock.ANY,
            EXPECTED_LINK,
            HEADERS,
            None,
            None,
            False,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )

    def test_download_to_filename_w_updated_wo_raw(self):
        updated = "2014-12-06T13:13:50.690Z"
        self._download_to_filename_helper(updated=updated, raw_download=False)

    def test_download_to_filename_wo_updated_wo_raw(self):
        self._download_to_filename_helper(updated=None, raw_download=False)

    def test_download_to_filename_w_updated_w_raw(self):
        updated = "2014-12-06T13:13:50.690Z"
        self._download_to_filename_helper(updated=updated, raw_download=True)

    def test_download_to_filename_wo_updated_w_raw(self):
        self._download_to_filename_helper(updated=None, raw_download=True)

    def test_download_to_filename_w_custom_timeout(self):
        self._download_to_filename_helper(
            updated=None, raw_download=False, timeout=9.58
        )

    def test_download_to_filename_corrupted(self):
        from google.resumable_media import DataCorruption

        blob_name = "blob-name"
        client = self._make_client()
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {"mediaLink": media_link}

        blob = self._make_one(blob_name, bucket=bucket, properties=properties)
        blob._do_download = mock.Mock()
        blob._do_download.side_effect = DataCorruption("testing")

        # Try to download into a temporary file (don't use
        # `_NamedTemporaryFile` it will try to remove after the file is
        # already removed)
        filehandle, filename = tempfile.mkstemp()
        os.close(filehandle)
        self.assertTrue(os.path.exists(filename))

        with self.assertRaises(DataCorruption):
            blob.download_to_filename(filename)

        # Make sure the file was cleaned up.
        self.assertFalse(os.path.exists(filename))

        headers = {"accept-encoding": "gzip"}
        blob._do_download.assert_called_once_with(
            client._http,
            mock.ANY,
            media_link,
            headers,
            None,
            None,
            False,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )
        stream = blob._do_download.mock_calls[0].args[1]
        self.assertEqual(stream.name, filename)

    def test_download_to_filename_w_key(self):
        from google.cloud._testing import _NamedTemporaryFile
        from google.cloud.storage.blob import _get_encryption_headers

        blob_name = "blob-name"
        # Create a fake client/bucket and use them in the Blob() constructor.
        client = self._make_client()
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {"mediaLink": media_link}
        key = b"aa426195405adee2c8081bb9e7e74b19"
        blob = self._make_one(
            blob_name, bucket=bucket, properties=properties, encryption_key=key
        )
        blob._do_download = mock.Mock()

        with _NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)

        headers = {"accept-encoding": "gzip"}
        headers.update(_get_encryption_headers(key))
        blob._do_download.assert_called_once_with(
            client._http,
            mock.ANY,
            media_link,
            headers,
            None,
            None,
            False,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )
        stream = blob._do_download.mock_calls[0].args[1]
        self.assertEqual(stream.name, temp.name)

    def _download_as_bytes_helper(self, raw_download, timeout=None):
        blob_name = "blob-name"
        client = self._make_client()
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {"mediaLink": media_link}
        blob = self._make_one(blob_name, bucket=bucket, properties=properties)
        blob._do_download = mock.Mock()

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            fetched = blob.download_as_bytes(raw_download=raw_download)
        else:
            expected_timeout = timeout
            fetched = blob.download_as_bytes(raw_download=raw_download, timeout=timeout)
        self.assertEqual(fetched, b"")

        headers = {"accept-encoding": "gzip"}
        blob._do_download.assert_called_once_with(
            client._http,
            mock.ANY,
            media_link,
            headers,
            None,
            None,
            raw_download,
            timeout=expected_timeout,
            checksum="md5",
        )
        stream = blob._do_download.mock_calls[0].args[1]
        self.assertIsInstance(stream, io.BytesIO)

    def test_download_as_string_w_response_headers(self):
        blob_name = "blob-name"
        client = mock.Mock(spec=["_http"])
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {"mediaLink": media_link}
        blob = self._make_one(blob_name, bucket=bucket, properties=properties)

        response = self._mock_requests_response(
            http_client.OK,
            headers={
                "Content-Type": "application/json",
                "Content-Language": "ko-kr",
                "Cache-Control": "max-age=1337;public",
                "Content-Encoding": "gzip",
                "X-Goog-Storage-Class": "STANDARD",
                "X-Goog-Hash": "crc32c=4gcgLQ==,md5=CS9tHYTtyFntzj7B9nkkJQ==",
            },
            # { "x": 5 } gzipped
            content=b"\x1f\x8b\x08\x00\xcfo\x17_\x02\xff\xabVP\xaaP\xb2R0U\xa8\x05\x00\xa1\xcaQ\x93\n\x00\x00\x00",
        )
        blob._extract_headers_from_download(response)

        self.assertEqual(blob.content_type, "application/json")
        self.assertEqual(blob.content_language, "ko-kr")
        self.assertEqual(blob.content_encoding, "gzip")
        self.assertEqual(blob.cache_control, "max-age=1337;public")
        self.assertEqual(blob.storage_class, "STANDARD")
        self.assertEqual(blob.md5_hash, "CS9tHYTtyFntzj7B9nkkJQ==")
        self.assertEqual(blob.crc32c, "4gcgLQ==")

        response = self._mock_requests_response(
            http_client.OK,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Language": "en-US",
                "Cache-Control": "max-age=1337;public",
                "Content-Encoding": "gzip",
                "X-Goog-Storage-Class": "STANDARD",
                "X-Goog-Hash": "crc32c=4/c+LQ==,md5=CS9tHYTt/+ntzj7B9nkkJQ==",
            },
            content=b"",
        )
        blob._extract_headers_from_download(response)
        self.assertEqual(blob.content_type, "application/octet-stream")
        self.assertEqual(blob.content_language, "en-US")
        self.assertEqual(blob.md5_hash, "CS9tHYTt/+ntzj7B9nkkJQ==")
        self.assertEqual(blob.crc32c, "4/c+LQ==")

    def test_download_as_string_w_hash_response_header_none(self):
        blob_name = "blob-name"
        md5_hash = "CS9tHYTtyFntzj7B9nkkJQ=="
        crc32c = "4gcgLQ=="
        client = mock.Mock(spec=["_http"])
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {
            "mediaLink": media_link,
            "md5Hash": md5_hash,
            "crc32c": crc32c,
        }
        blob = self._make_one(blob_name, bucket=bucket, properties=properties)

        response = self._mock_requests_response(
            http_client.OK,
            headers={"X-Goog-Hash": ""},
            # { "x": 5 } gzipped
            content=b"\x1f\x8b\x08\x00\xcfo\x17_\x02\xff\xabVP\xaaP\xb2R0U\xa8\x05\x00\xa1\xcaQ\x93\n\x00\x00\x00",
        )
        blob._extract_headers_from_download(response)

        self.assertEqual(blob.md5_hash, md5_hash)
        self.assertEqual(blob.crc32c, crc32c)

    def test_download_as_string_w_response_headers_not_match(self):
        blob_name = "blob-name"
        client = mock.Mock(spec=["_http"])
        bucket = _Bucket(client)
        media_link = "http://example.com/media/"
        properties = {"mediaLink": media_link}
        blob = self._make_one(blob_name, bucket=bucket, properties=properties)

        response = self._mock_requests_response(
            http_client.OK,
            headers={"X-Goog-Hash": "bogus=4gcgLQ==,"},
            # { "x": 5 } gzipped
            content=b"",
        )
        blob._extract_headers_from_download(response)

        self.assertIsNone(blob.md5_hash)
        self.assertIsNone(blob.crc32c)

    def test_download_as_bytes_w_generation_match(self):
        GENERATION_NUMBER = 6
        MEDIA_LINK = "http://example.com/media/"

        client = self._make_client()
        blob = self._make_one(
            "blob-name", bucket=_Bucket(client), properties={"mediaLink": MEDIA_LINK}
        )
        client.download_blob_to_file = mock.Mock()

        fetched = blob.download_as_bytes(if_generation_match=GENERATION_NUMBER)
        self.assertEqual(fetched, b"")

        client.download_blob_to_file.assert_called_once_with(
            blob,
            mock.ANY,
            start=None,
            end=None,
            raw_download=False,
            if_generation_match=GENERATION_NUMBER,
            if_generation_not_match=None,
            if_metageneration_match=None,
            if_metageneration_not_match=None,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )

    def test_download_as_bytes_wo_raw(self):
        self._download_as_bytes_helper(raw_download=False)

    def test_download_as_bytes_w_raw(self):
        self._download_as_bytes_helper(raw_download=True)

    def test_download_as_byte_w_custom_timeout(self):
        self._download_as_bytes_helper(raw_download=False, timeout=9.58)

    def _download_as_text_helper(
        self,
        raw_download,
        client=None,
        start=None,
        end=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
        encoding=None,
        charset=None,
        no_charset=False,
        expected_value=u"DEADBEEF",
        payload=None,
    ):
        if payload is None:
            if encoding is not None:
                payload = expected_value.encode(encoding)
            else:
                payload = expected_value.encode()

        blob_name = "blob-name"
        bucket = _Bucket()

        properties = {}
        if charset is not None:
            properties["contentType"] = "text/plain; charset={}".format(charset)
        elif no_charset:
            properties = {"contentType": "text/plain"}

        blob = self._make_one(blob_name, bucket=bucket, properties=properties)
        blob.download_as_bytes = mock.Mock(return_value=payload)

        kwargs = {"raw_download": raw_download}

        if client is not None:
            kwargs["client"] = client

        if start is not None:
            kwargs["start"] = start

        if end is not None:
            kwargs["end"] = end

        if encoding is not None:
            kwargs["encoding"] = encoding

        if if_generation_match is not None:
            kwargs["if_generation_match"] = if_generation_match

        if if_generation_not_match is not None:
            kwargs["if_generation_not_match"] = if_generation_not_match

        if if_metageneration_match is not None:
            kwargs["if_metageneration_match"] = if_metageneration_match

        if if_metageneration_not_match is not None:
            kwargs["if_metageneration_not_match"] = if_metageneration_not_match

        if timeout is None:
            expected_timeout = self._get_default_timeout()
        else:
            kwargs["timeout"] = expected_timeout = timeout

        fetched = blob.download_as_text(**kwargs)

        self.assertEqual(fetched, expected_value)

        blob.download_as_bytes.assert_called_once_with(
            client=client,
            start=start,
            end=end,
            raw_download=raw_download,
            timeout=expected_timeout,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
        )

    def test_download_as_text_wo_raw(self):
        self._download_as_text_helper(raw_download=False)

    def test_download_as_text_w_raw(self):
        self._download_as_text_helper(raw_download=True)

    def test_download_as_text_w_client(self):
        self._download_as_text_helper(raw_download=False, client=object())

    def test_download_as_text_w_start(self):
        self._download_as_text_helper(raw_download=False, start=123)

    def test_download_as_text_w_end(self):
        self._download_as_text_helper(raw_download=False, end=456)

    def test_download_as_text_w_custom_timeout(self):
        self._download_as_text_helper(raw_download=False, timeout=9.58)

    def test_download_as_text_w_if_generation_match(self):
        self._download_as_text_helper(raw_download=False, if_generation_match=6)

    def test_download_as_text_w_if_generation_not_match(self):
        self._download_as_text_helper(raw_download=False, if_generation_not_match=6)

    def test_download_as_text_w_if_metageneration_match(self):
        self._download_as_text_helper(raw_download=False, if_metageneration_match=6)

    def test_download_as_text_w_if_metageneration_not_match(self):
        self._download_as_text_helper(raw_download=False, if_metageneration_not_match=6)

    def test_download_as_text_w_encoding(self):
        encoding = "utf-16"
        self._download_as_text_helper(
            raw_download=False, encoding=encoding,
        )

    def test_download_as_text_w_no_charset(self):
        self._download_as_text_helper(
            raw_download=False, no_charset=True,
        )

    def test_download_as_text_w_non_ascii_w_explicit_encoding(self):
        expected_value = u"\x0AFe"
        encoding = "utf-16"
        charset = "latin1"
        payload = expected_value.encode(encoding)
        self._download_as_text_helper(
            raw_download=False,
            expected_value=expected_value,
            payload=payload,
            encoding=encoding,
            charset=charset,
        )

    def test_download_as_text_w_non_ascii_wo_explicit_encoding_w_charset(self):
        expected_value = u"\x0AFe"
        charset = "utf-16"
        payload = expected_value.encode(charset)
        self._download_as_text_helper(
            raw_download=False,
            expected_value=expected_value,
            payload=payload,
            charset=charset,
        )

    @mock.patch("warnings.warn")
    def test_download_as_string(self, mock_warn):
        MEDIA_LINK = "http://example.com/media/"

        client = self._make_client()
        blob = self._make_one(
            "blob-name", bucket=_Bucket(client), properties={"mediaLink": MEDIA_LINK}
        )
        client.download_blob_to_file = mock.Mock()

        fetched = blob.download_as_string()
        self.assertEqual(fetched, b"")

        client.download_blob_to_file.assert_called_once_with(
            blob,
            mock.ANY,
            start=None,
            end=None,
            raw_download=False,
            if_generation_match=None,
            if_generation_not_match=None,
            if_metageneration_match=None,
            if_metageneration_not_match=None,
            timeout=self._get_default_timeout(),
            checksum="md5",
        )

        mock_warn.assert_called_with(
            "Blob.download_as_string() is deprecated and will be removed in future."
            "Use Blob.download_as_bytes() instead.",
            PendingDeprecationWarning,
            stacklevel=1,
        )

    def test__get_content_type_explicit(self):
        blob = self._make_one(u"blob-name", bucket=None)

        content_type = u"text/plain"
        return_value = blob._get_content_type(content_type)
        self.assertEqual(return_value, content_type)

    def test__get_content_type_from_blob(self):
        blob = self._make_one(u"blob-name", bucket=None)
        blob.content_type = u"video/mp4"

        return_value = blob._get_content_type(None)
        self.assertEqual(return_value, blob.content_type)

    def test__get_content_type_from_filename(self):
        blob = self._make_one(u"blob-name", bucket=None)

        return_value = blob._get_content_type(None, filename="archive.tar")
        self.assertEqual(return_value, "application/x-tar")

    def test__get_content_type_default(self):
        blob = self._make_one(u"blob-name", bucket=None)

        return_value = blob._get_content_type(None)
        self.assertEqual(return_value, u"application/octet-stream")

    def test__get_writable_metadata_no_changes(self):
        name = u"blob-name"
        blob = self._make_one(name, bucket=None)

        object_metadata = blob._get_writable_metadata()
        expected = {"name": name}
        self.assertEqual(object_metadata, expected)

    def test__get_writable_metadata_with_changes(self):
        name = u"blob-name"
        blob = self._make_one(name, bucket=None)
        blob.storage_class = "NEARLINE"
        blob.cache_control = "max-age=3600"
        blob.metadata = {"color": "red"}

        object_metadata = blob._get_writable_metadata()
        expected = {
            "cacheControl": blob.cache_control,
            "metadata": blob.metadata,
            "name": name,
            "storageClass": blob.storage_class,
        }
        self.assertEqual(object_metadata, expected)

    def test__get_writable_metadata_unwritable_field(self):
        name = u"blob-name"
        properties = {"updated": "2016-10-16T18:18:18.181Z"}
        blob = self._make_one(name, bucket=None, properties=properties)
        # Fake that `updated` is in changes.
        blob._changes.add("updated")

        object_metadata = blob._get_writable_metadata()
        expected = {"name": name}
        self.assertEqual(object_metadata, expected)

    def test__set_metadata_to_none(self):
        name = u"blob-name"
        blob = self._make_one(name, bucket=None)
        blob.storage_class = "NEARLINE"
        blob.cache_control = "max-age=3600"

        with mock.patch("google.cloud.storage.blob.Blob._patch_property") as patch_prop:
            blob.metadata = None
            patch_prop.assert_called_once_with("metadata", None)

    def test__get_upload_arguments(self):
        name = u"blob-name"
        key = b"[pXw@,p@@AfBfrR3x-2b2SCHR,.?YwRO"
        blob = self._make_one(name, bucket=None, encryption_key=key)
        blob.content_disposition = "inline"

        content_type = u"image/jpeg"
        info = blob._get_upload_arguments(content_type)

        headers, object_metadata, new_content_type = info
        header_key_value = "W3BYd0AscEBAQWZCZnJSM3gtMmIyU0NIUiwuP1l3Uk8="
        header_key_hash_value = "G0++dxF4q5rG4o9kE8gvEKn15RH6wLm0wXV1MgAlXOg="
        expected_headers = {
            "X-Goog-Encryption-Algorithm": "AES256",
            "X-Goog-Encryption-Key": header_key_value,
            "X-Goog-Encryption-Key-Sha256": header_key_hash_value,
        }
        self.assertEqual(headers, expected_headers)
        expected_metadata = {
            "contentDisposition": blob.content_disposition,
            "name": name,
        }
        self.assertEqual(object_metadata, expected_metadata)
        self.assertEqual(new_content_type, content_type)

    def _mock_transport(self, status_code, headers, content=b""):
        fake_transport = mock.Mock(spec=["request"])
        fake_response = self._mock_requests_response(
            status_code, headers, content=content
        )
        fake_transport.request.return_value = fake_response
        return fake_transport

    def _do_multipart_success(
        self,
        mock_get_boundary,
        client=None,
        size=None,
        num_retries=None,
        user_project=None,
        predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        kms_key_name=None,
        timeout=None,
        metadata=None,
    ):
        from six.moves.urllib.parse import urlencode

        bucket = _Bucket(name="w00t", user_project=user_project)
        blob = self._make_one(u"blob-name", bucket=bucket, kms_key_name=kms_key_name)
        self.assertIsNone(blob.chunk_size)
        if metadata:
            self.assertIsNone(blob.metadata)
            blob._properties["metadata"] = metadata
            self.assertEqual(len(blob._changes), 0)

        # Create some mock arguments.
        if not client:
            # Create mocks to be checked for doing transport.
            transport = self._mock_transport(http_client.OK, {})

            client = mock.Mock(_http=transport, _connection=_Connection, spec=["_http"])
            client._connection.API_BASE_URL = "https://storage.googleapis.com"
        data = b"data here hear hier"
        stream = io.BytesIO(data)
        content_type = u"application/xml"

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        response = blob._do_multipart_upload(
            client,
            stream,
            content_type,
            size,
            num_retries,
            predefined_acl,
            if_generation_match,
            if_generation_not_match,
            if_metageneration_match,
            if_metageneration_not_match,
            **timeout_kwarg
        )

        # Check the mocks and the returned value.
        self.assertIs(response, client._http.request.return_value)
        if size is None:
            data_read = data
            self.assertEqual(stream.tell(), len(data))
        else:
            data_read = data[:size]
            self.assertEqual(stream.tell(), size)

        mock_get_boundary.assert_called_once_with()

        upload_url = (
            "https://storage.googleapis.com/upload/storage/v1" + bucket.path + "/o"
        )

        qs_params = [("uploadType", "multipart")]

        if user_project is not None:
            qs_params.append(("userProject", user_project))

        if predefined_acl is not None:
            qs_params.append(("predefinedAcl", predefined_acl))

        if kms_key_name is not None and "cryptoKeyVersions" not in kms_key_name:
            qs_params.append(("kmsKeyName", kms_key_name))

        if if_generation_match is not None:
            qs_params.append(("ifGenerationMatch", if_generation_match))

        if if_generation_not_match is not None:
            qs_params.append(("ifGenerationNotMatch", if_generation_not_match))

        if if_metageneration_match is not None:
            qs_params.append(("ifMetagenerationMatch", if_metageneration_match))

        if if_metageneration_not_match is not None:
            qs_params.append(("ifMetaGenerationNotMatch", if_metageneration_not_match))

        upload_url += "?" + urlencode(qs_params)

        blob_data = {"name": "blob-name"}
        if metadata:
            blob_data["metadata"] = metadata
            self.assertEqual(blob._changes, set(["metadata"]))
        payload = (
            b"--==0==\r\n"
            + b"content-type: application/json; charset=UTF-8\r\n\r\n"
            + json.dumps(blob_data).encode("utf-8")
            + b"\r\n--==0==\r\n"
            + b"content-type: application/xml\r\n\r\n"
            + data_read
            + b"\r\n--==0==--"
        )
        headers = {"content-type": b'multipart/related; boundary="==0=="'}
        client._http.request.assert_called_once_with(
            "POST", upload_url, data=payload, headers=headers, timeout=expected_timeout
        )

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_no_size(self, mock_get_boundary):
        self._do_multipart_success(mock_get_boundary, predefined_acl="private")

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_size(self, mock_get_boundary):
        self._do_multipart_success(mock_get_boundary, size=10)

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_user_project(self, mock_get_boundary):
        user_project = "user-project-123"
        self._do_multipart_success(mock_get_boundary, user_project=user_project)

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_kms(self, mock_get_boundary):
        kms_resource = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
        )
        self._do_multipart_success(mock_get_boundary, kms_key_name=kms_resource)

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_kms_with_version(self, mock_get_boundary):
        kms_resource = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
            "cryptoKeyVersions/1"
        )
        self._do_multipart_success(mock_get_boundary, kms_key_name=kms_resource)

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_retry(self, mock_get_boundary):
        self._do_multipart_success(mock_get_boundary, num_retries=8)

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_generation_match(self, mock_get_boundary):
        self._do_multipart_success(
            mock_get_boundary, if_generation_match=4, if_metageneration_match=4
        )

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_custom_timeout(self, mock_get_boundary):
        self._do_multipart_success(mock_get_boundary, timeout=9.58)

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_generation_not_match(self, mock_get_boundary):
        self._do_multipart_success(
            mock_get_boundary, if_generation_not_match=4, if_metageneration_not_match=4
        )

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_client(self, mock_get_boundary):
        transport = self._mock_transport(http_client.OK, {})
        client = mock.Mock(_http=transport, _connection=_Connection, spec=["_http"])
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        self._do_multipart_success(mock_get_boundary, client=client)

    @mock.patch(u"google.resumable_media._upload.get_boundary", return_value=b"==0==")
    def test__do_multipart_upload_with_metadata(self, mock_get_boundary):
        self._do_multipart_success(mock_get_boundary, metadata={"test": "test"})

    def test__do_multipart_upload_bad_size(self):
        blob = self._make_one(u"blob-name", bucket=None)

        data = b"data here hear hier"
        stream = io.BytesIO(data)
        size = 50
        self.assertGreater(size, len(data))

        with self.assertRaises(ValueError) as exc_info:
            blob._do_multipart_upload(
                None, stream, None, size, None, None, None, None, None, None
            )

        exc_contents = str(exc_info.exception)
        self.assertIn("was specified but the file-like object only had", exc_contents)
        self.assertEqual(stream.tell(), len(data))

    def _initiate_resumable_helper(
        self,
        client=None,
        size=None,
        extra_headers=None,
        chunk_size=None,
        num_retries=None,
        user_project=None,
        predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        blob_chunk_size=786432,
        kms_key_name=None,
        timeout=None,
        metadata=None,
    ):
        from six.moves.urllib.parse import urlencode
        from google.resumable_media.requests import ResumableUpload
        from google.cloud.storage.blob import _DEFAULT_CHUNKSIZE

        bucket = _Bucket(name="whammy", user_project=user_project)
        blob = self._make_one(u"blob-name", bucket=bucket, kms_key_name=kms_key_name)
        if metadata:
            self.assertIsNone(blob.metadata)
            blob._properties["metadata"] = metadata
            self.assertEqual(len(blob._changes), 0)
        else:
            blob.metadata = {"rook": "takes knight"}
        blob.chunk_size = blob_chunk_size
        if blob_chunk_size is not None:
            self.assertIsNotNone(blob.chunk_size)
        else:
            self.assertIsNone(blob.chunk_size)

        # Need to make sure **same** dict is used because ``json.dumps()``
        # will depend on the hash order.
        if not metadata:
            object_metadata = blob._get_writable_metadata()
            blob._get_writable_metadata = mock.Mock(
                return_value=object_metadata, spec=[]
            )

        resumable_url = "http://test.invalid?upload_id=hey-you"
        if not client:
            # Create mocks to be checked for doing transport.
            response_headers = {"location": resumable_url}
            transport = self._mock_transport(http_client.OK, response_headers)

            # Create some mock arguments and call the method under test.
            client = mock.Mock(
                _http=transport, _connection=_Connection, spec=[u"_http"]
            )
            client._connection.API_BASE_URL = "https://storage.googleapis.com"
        data = b"hello hallo halo hi-low"
        stream = io.BytesIO(data)
        content_type = u"text/plain"

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        upload, transport = blob._initiate_resumable_upload(
            client,
            stream,
            content_type,
            size,
            num_retries,
            extra_headers=extra_headers,
            chunk_size=chunk_size,
            predefined_acl=predefined_acl,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            **timeout_kwarg
        )

        # Check the returned values.
        self.assertIsInstance(upload, ResumableUpload)

        upload_url = (
            "https://storage.googleapis.com/upload/storage/v1" + bucket.path + "/o"
        )
        qs_params = [("uploadType", "resumable")]

        if user_project is not None:
            qs_params.append(("userProject", user_project))

        if predefined_acl is not None:
            qs_params.append(("predefinedAcl", predefined_acl))

        if kms_key_name is not None and "cryptoKeyVersions" not in kms_key_name:
            qs_params.append(("kmsKeyName", kms_key_name))

        if if_generation_match is not None:
            qs_params.append(("ifGenerationMatch", if_generation_match))

        if if_generation_not_match is not None:
            qs_params.append(("ifGenerationNotMatch", if_generation_not_match))

        if if_metageneration_match is not None:
            qs_params.append(("ifMetagenerationMatch", if_metageneration_match))

        if if_metageneration_not_match is not None:
            qs_params.append(("ifMetaGenerationNotMatch", if_metageneration_not_match))

        upload_url += "?" + urlencode(qs_params)

        self.assertEqual(upload.upload_url, upload_url)
        if extra_headers is None:
            self.assertEqual(upload._headers, {})
        else:
            self.assertEqual(upload._headers, extra_headers)
            self.assertIsNot(upload._headers, extra_headers)
        self.assertFalse(upload.finished)
        if chunk_size is None:
            if blob_chunk_size is None:
                self.assertEqual(upload._chunk_size, _DEFAULT_CHUNKSIZE)
            else:
                self.assertEqual(upload._chunk_size, blob.chunk_size)
        else:
            self.assertNotEqual(blob.chunk_size, chunk_size)
            self.assertEqual(upload._chunk_size, chunk_size)
        self.assertIs(upload._stream, stream)
        if metadata:
            self.assertEqual(blob._changes, set(["metadata"]))
        if size is None:
            self.assertIsNone(upload._total_bytes)
        else:
            self.assertEqual(upload._total_bytes, size)
        self.assertEqual(upload._content_type, content_type)
        self.assertEqual(upload.resumable_url, resumable_url)
        retry_strategy = upload._retry_strategy
        self.assertEqual(retry_strategy.max_sleep, 64.0)
        if num_retries is None:
            self.assertEqual(retry_strategy.max_cumulative_retry, 600.0)
            self.assertIsNone(retry_strategy.max_retries)
        else:
            self.assertIsNone(retry_strategy.max_cumulative_retry)
            self.assertEqual(retry_strategy.max_retries, num_retries)
        self.assertIs(client._http, transport)
        # Make sure we never read from the stream.
        self.assertEqual(stream.tell(), 0)

        if metadata:
            object_metadata = {"name": u"blob-name", "metadata": metadata}
        else:
            # Check the mocks.
            blob._get_writable_metadata.assert_called_once_with()
        payload = json.dumps(object_metadata).encode("utf-8")
        expected_headers = {
            "content-type": "application/json; charset=UTF-8",
            "x-upload-content-type": content_type,
        }
        if size is not None:
            expected_headers["x-upload-content-length"] = str(size)
        if extra_headers is not None:
            expected_headers.update(extra_headers)
        transport.request.assert_called_once_with(
            "POST",
            upload_url,
            data=payload,
            headers=expected_headers,
            timeout=expected_timeout,
        )

    def test__initiate_resumable_upload_with_metadata(self):
        self._initiate_resumable_helper(metadata={"test": "test"})

    def test__initiate_resumable_upload_with_custom_timeout(self):
        self._initiate_resumable_helper(timeout=9.58)

    def test__initiate_resumable_upload_no_size(self):
        self._initiate_resumable_helper()

    def test__initiate_resumable_upload_with_size(self):
        self._initiate_resumable_helper(size=10000)

    def test__initiate_resumable_upload_with_user_project(self):
        user_project = "user-project-123"
        self._initiate_resumable_helper(user_project=user_project)

    def test__initiate_resumable_upload_with_kms(self):
        kms_resource = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
        )
        self._initiate_resumable_helper(kms_key_name=kms_resource)

    def test__initiate_resumable_upload_with_kms_with_version(self):
        kms_resource = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
            "cryptoKeyVersions/1"
        )
        self._initiate_resumable_helper(kms_key_name=kms_resource)

    def test__initiate_resumable_upload_without_chunk_size(self):
        self._initiate_resumable_helper(blob_chunk_size=None)

    def test__initiate_resumable_upload_with_chunk_size(self):
        one_mb = 1048576
        self._initiate_resumable_helper(chunk_size=one_mb)

    def test__initiate_resumable_upload_with_extra_headers(self):
        extra_headers = {"origin": "http://not-in-kansas-anymore.invalid"}
        self._initiate_resumable_helper(extra_headers=extra_headers)

    def test__initiate_resumable_upload_with_retry(self):
        self._initiate_resumable_helper(num_retries=11)

    def test__initiate_resumable_upload_with_generation_match(self):
        self._initiate_resumable_helper(
            if_generation_match=4, if_metageneration_match=4
        )

    def test__initiate_resumable_upload_with_generation_not_match(self):
        self._initiate_resumable_helper(
            if_generation_not_match=4, if_metageneration_not_match=4
        )

    def test__initiate_resumable_upload_with_predefined_acl(self):
        self._initiate_resumable_helper(predefined_acl="private")

    def test__initiate_resumable_upload_with_client(self):
        resumable_url = "http://test.invalid?upload_id=hey-you"
        response_headers = {"location": resumable_url}
        transport = self._mock_transport(http_client.OK, response_headers)

        client = mock.Mock(_http=transport, _connection=_Connection, spec=[u"_http"])
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        self._initiate_resumable_helper(client=client)

    def _make_resumable_transport(
        self, headers1, headers2, headers3, total_bytes, data_corruption=False
    ):
        from google import resumable_media

        fake_transport = mock.Mock(spec=["request"])

        fake_response1 = self._mock_requests_response(http_client.OK, headers1)
        fake_response2 = self._mock_requests_response(
            resumable_media.PERMANENT_REDIRECT, headers2
        )
        json_body = '{{"size": "{:d}"}}'.format(total_bytes)
        if data_corruption:
            fake_response3 = resumable_media.DataCorruption(None)
        else:
            fake_response3 = self._mock_requests_response(
                http_client.OK, headers3, content=json_body.encode("utf-8")
            )

        responses = [fake_response1, fake_response2, fake_response3]
        fake_transport.request.side_effect = responses
        return fake_transport, responses

    @staticmethod
    def _do_resumable_upload_call0(
        blob,
        content_type,
        size=None,
        predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
    ):
        # First mock transport.request() does initiates upload.
        upload_url = (
            "https://storage.googleapis.com/upload/storage/v1"
            + blob.bucket.path
            + "/o?uploadType=resumable"
        )
        if predefined_acl is not None:
            upload_url += "&predefinedAcl={}".format(predefined_acl)
        expected_headers = {
            "content-type": "application/json; charset=UTF-8",
            "x-upload-content-type": content_type,
        }
        if size is not None:
            expected_headers["x-upload-content-length"] = str(size)
        payload = json.dumps({"name": blob.name}).encode("utf-8")
        return mock.call(
            "POST", upload_url, data=payload, headers=expected_headers, timeout=timeout
        )

    @staticmethod
    def _do_resumable_upload_call1(
        blob,
        content_type,
        data,
        resumable_url,
        size=None,
        predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
    ):
        # Second mock transport.request() does sends first chunk.
        if size is None:
            content_range = "bytes 0-{:d}/*".format(blob.chunk_size - 1)
        else:
            content_range = "bytes 0-{:d}/{:d}".format(blob.chunk_size - 1, size)

        expected_headers = {
            "content-type": content_type,
            "content-range": content_range,
        }
        payload = data[: blob.chunk_size]
        return mock.call(
            "PUT",
            resumable_url,
            data=payload,
            headers=expected_headers,
            timeout=timeout,
        )

    @staticmethod
    def _do_resumable_upload_call2(
        blob,
        content_type,
        data,
        resumable_url,
        total_bytes,
        predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
    ):
        # Third mock transport.request() does sends last chunk.
        content_range = "bytes {:d}-{:d}/{:d}".format(
            blob.chunk_size, total_bytes - 1, total_bytes
        )
        expected_headers = {
            "content-type": content_type,
            "content-range": content_range,
        }
        payload = data[blob.chunk_size :]
        return mock.call(
            "PUT",
            resumable_url,
            data=payload,
            headers=expected_headers,
            timeout=timeout,
        )

    def _do_resumable_helper(
        self,
        use_size=False,
        num_retries=None,
        predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
        data_corruption=False,
    ):
        bucket = _Bucket(name="yesterday")
        blob = self._make_one(u"blob-name", bucket=bucket)
        blob.chunk_size = blob._CHUNK_SIZE_MULTIPLE
        self.assertIsNotNone(blob.chunk_size)

        # Data to be uploaded.
        data = b"<html>" + (b"A" * blob.chunk_size) + b"</html>"
        total_bytes = len(data)
        if use_size:
            size = total_bytes
        else:
            size = None

        # Create mocks to be checked for doing transport.
        resumable_url = "http://test.invalid?upload_id=and-then-there-was-1"
        headers1 = {"location": resumable_url}
        headers2 = {"range": "bytes=0-{:d}".format(blob.chunk_size - 1)}
        transport, responses = self._make_resumable_transport(
            headers1, headers2, {}, total_bytes, data_corruption=data_corruption
        )

        # Create some mock arguments and call the method under test.
        client = mock.Mock(_http=transport, _connection=_Connection, spec=["_http"])
        client._connection.API_BASE_URL = "https://storage.googleapis.com"
        stream = io.BytesIO(data)
        content_type = u"text/html"

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        response = blob._do_resumable_upload(
            client,
            stream,
            content_type,
            size,
            num_retries,
            predefined_acl,
            if_generation_match,
            if_generation_not_match,
            if_metageneration_match,
            if_metageneration_not_match,
            **timeout_kwarg
        )

        # Check the returned values.
        self.assertIs(response, responses[2])
        self.assertEqual(stream.tell(), total_bytes)

        # Check the mocks.
        call0 = self._do_resumable_upload_call0(
            blob,
            content_type,
            size=size,
            predefined_acl=predefined_acl,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            timeout=expected_timeout,
        )
        call1 = self._do_resumable_upload_call1(
            blob,
            content_type,
            data,
            resumable_url,
            size=size,
            predefined_acl=predefined_acl,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            timeout=expected_timeout,
        )
        call2 = self._do_resumable_upload_call2(
            blob,
            content_type,
            data,
            resumable_url,
            total_bytes,
            predefined_acl=predefined_acl,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            timeout=expected_timeout,
        )
        self.assertEqual(transport.request.mock_calls, [call0, call1, call2])

    def test__do_resumable_upload_with_custom_timeout(self):
        self._do_resumable_helper(timeout=9.58)

    def test__do_resumable_upload_no_size(self):
        self._do_resumable_helper()

    def test__do_resumable_upload_with_size(self):
        self._do_resumable_helper(use_size=True)

    def test__do_resumable_upload_with_retry(self):
        self._do_resumable_helper(num_retries=6)

    def test__do_resumable_upload_with_predefined_acl(self):
        self._do_resumable_helper(predefined_acl="private")

    def test__do_resumable_upload_with_data_corruption(self):
        from google.resumable_media import DataCorruption

        with mock.patch("google.cloud.storage.blob.Blob.delete") as patch:
            try:
                self._do_resumable_helper(data_corruption=True)
            except Exception as e:
                self.assertTrue(patch.called)
                self.assertIsInstance(e, DataCorruption)

    def _do_upload_helper(
        self,
        chunk_size=None,
        num_retries=None,
        predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        size=None,
        timeout=None,
    ):
        from google.cloud.storage.blob import _MAX_MULTIPART_SIZE

        blob = self._make_one(u"blob-name", bucket=None)

        # Create a fake response.
        response = mock.Mock(spec=[u"json"])
        response.json.return_value = mock.sentinel.json
        # Mock **both** helpers.
        blob._do_multipart_upload = mock.Mock(return_value=response, spec=[])
        blob._do_resumable_upload = mock.Mock(return_value=response, spec=[])

        if chunk_size is None:
            self.assertIsNone(blob.chunk_size)
        else:
            blob.chunk_size = chunk_size
            self.assertIsNotNone(blob.chunk_size)

        client = mock.sentinel.client
        stream = mock.sentinel.stream
        content_type = u"video/mp4"
        if size is None:
            size = 12345654321

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        # Make the request and check the mocks.
        created_json = blob._do_upload(
            client,
            stream,
            content_type,
            size,
            num_retries,
            predefined_acl,
            if_generation_match,
            if_generation_not_match,
            if_metageneration_match,
            if_metageneration_not_match,
            **timeout_kwarg
        )

        # Adjust num_retries expectations to reflect the conditional default in
        # _do_upload()
        if num_retries is None and if_metageneration_match is None:
            num_retries = 0

        self.assertIs(created_json, mock.sentinel.json)
        response.json.assert_called_once_with()
        if size is not None and size <= _MAX_MULTIPART_SIZE:
            blob._do_multipart_upload.assert_called_once_with(
                client,
                stream,
                content_type,
                size,
                num_retries,
                predefined_acl,
                if_generation_match,
                if_generation_not_match,
                if_metageneration_match,
                if_metageneration_not_match,
                timeout=expected_timeout,
                checksum=None,
            )
            blob._do_resumable_upload.assert_not_called()
        else:
            blob._do_multipart_upload.assert_not_called()
            blob._do_resumable_upload.assert_called_once_with(
                client,
                stream,
                content_type,
                size,
                num_retries,
                predefined_acl,
                if_generation_match,
                if_generation_not_match,
                if_metageneration_match,
                if_metageneration_not_match,
                timeout=expected_timeout,
                checksum=None,
            )

    def test__do_upload_uses_multipart(self):
        from google.cloud.storage.blob import _MAX_MULTIPART_SIZE

        self._do_upload_helper(size=_MAX_MULTIPART_SIZE)

    def test__do_upload_uses_multipart_w_custom_timeout(self):
        from google.cloud.storage.blob import _MAX_MULTIPART_SIZE

        self._do_upload_helper(size=_MAX_MULTIPART_SIZE, timeout=9.58)

    def test__do_upload_uses_resumable(self):
        from google.cloud.storage.blob import _MAX_MULTIPART_SIZE

        chunk_size = 256 * 1024  # 256KB
        self._do_upload_helper(chunk_size=chunk_size, size=_MAX_MULTIPART_SIZE + 1)

    def test__do_upload_uses_resumable_w_custom_timeout(self):
        from google.cloud.storage.blob import _MAX_MULTIPART_SIZE

        chunk_size = 256 * 1024  # 256KB
        self._do_upload_helper(
            chunk_size=chunk_size, size=_MAX_MULTIPART_SIZE + 1, timeout=9.58
        )

    def test__do_upload_with_retry(self):
        self._do_upload_helper(num_retries=20)

    def _upload_from_file_helper(self, side_effect=None, **kwargs):
        from google.cloud._helpers import UTC

        blob = self._make_one("blob-name", bucket=None)
        # Mock low-level upload helper on blob (it is tested elsewhere).
        created_json = {"updated": "2017-01-01T09:09:09.081Z"}
        blob._do_upload = mock.Mock(return_value=created_json, spec=[])
        if side_effect is not None:
            blob._do_upload.side_effect = side_effect
        # Make sure `updated` is empty before the request.
        self.assertIsNone(blob.updated)

        data = b"data is here"
        stream = io.BytesIO(data)
        stream.seek(2)  # Not at zero.
        content_type = u"font/woff"
        client = mock.sentinel.client
        predefined_acl = kwargs.get("predefined_acl", None)
        if_generation_match = kwargs.get("if_generation_match", None)
        if_generation_not_match = kwargs.get("if_generation_not_match", None)
        if_metageneration_match = kwargs.get("if_metageneration_match", None)
        if_metageneration_not_match = kwargs.get("if_metageneration_not_match", None)
        ret_val = blob.upload_from_file(
            stream, size=len(data), content_type=content_type, client=client, **kwargs
        )

        # Check the response and side-effects.
        self.assertIsNone(ret_val)
        new_updated = datetime.datetime(2017, 1, 1, 9, 9, 9, 81000, tzinfo=UTC)
        self.assertEqual(blob.updated, new_updated)

        expected_timeout = kwargs.get("timeout", self._get_default_timeout())

        # Check the mock.
        num_retries = kwargs.get("num_retries")
        blob._do_upload.assert_called_once_with(
            client,
            stream,
            content_type,
            len(data),
            num_retries,
            predefined_acl,
            if_generation_match,
            if_generation_not_match,
            if_metageneration_match,
            if_metageneration_not_match,
            timeout=expected_timeout,
            checksum=None,
        )
        return stream

    def test_upload_from_file_success(self):
        stream = self._upload_from_file_helper(predefined_acl="private")
        assert stream.tell() == 2

    @mock.patch("warnings.warn")
    def test_upload_from_file_with_retries(self, mock_warn):
        from google.cloud.storage import blob as blob_module

        self._upload_from_file_helper(num_retries=20)
        mock_warn.assert_called_once_with(
            blob_module._NUM_RETRIES_MESSAGE, DeprecationWarning, stacklevel=2
        )

    def test_upload_from_file_with_rewind(self):
        stream = self._upload_from_file_helper(rewind=True)
        assert stream.tell() == 0

    def test_upload_from_file_with_custom_timeout(self):
        self._upload_from_file_helper(timeout=9.58)

    def test_upload_from_file_failure(self):
        import requests

        from google.resumable_media import InvalidResponse
        from google.cloud import exceptions

        message = "Someone is already in this spot."
        response = requests.Response()
        response.status_code = http_client.CONFLICT
        response.request = requests.Request("POST", "http://example.com").prepare()
        side_effect = InvalidResponse(response, message)

        with self.assertRaises(exceptions.Conflict) as exc_info:
            self._upload_from_file_helper(side_effect=side_effect)

        self.assertIn(message, exc_info.exception.message)
        self.assertEqual(exc_info.exception.errors, [])

    def _do_upload_mock_call_helper(
        self, blob, client, content_type, size, timeout=None
    ):
        self.assertEqual(blob._do_upload.call_count, 1)
        mock_call = blob._do_upload.mock_calls[0]
        call_name, pos_args, kwargs = mock_call
        self.assertEqual(call_name, "")
        self.assertEqual(len(pos_args), 10)
        self.assertEqual(pos_args[0], client)
        self.assertEqual(pos_args[2], content_type)
        self.assertEqual(pos_args[3], size)
        self.assertIsNone(pos_args[4])  # num_retries
        self.assertIsNone(pos_args[5])  # predefined_acl
        self.assertIsNone(pos_args[6])  # if_generation_match
        self.assertIsNone(pos_args[7])  # if_generation_not_match
        self.assertIsNone(pos_args[8])  # if_metageneration_match
        self.assertIsNone(pos_args[9])  # if_metageneration_not_match

        expected_timeout = self._get_default_timeout() if timeout is None else timeout
        self.assertEqual(kwargs, {"timeout": expected_timeout, "checksum": None})

        return pos_args[1]

    def test_upload_from_filename(self):
        from google.cloud._testing import _NamedTemporaryFile

        blob = self._make_one("blob-name", bucket=None)
        # Mock low-level upload helper on blob (it is tested elsewhere).
        created_json = {"metadata": {"mint": "ice-cream"}}
        blob._do_upload = mock.Mock(return_value=created_json, spec=[])
        # Make sure `metadata` is empty before the request.
        self.assertIsNone(blob.metadata)

        data = b"soooo much data"
        content_type = u"image/svg+xml"
        client = mock.sentinel.client
        with _NamedTemporaryFile() as temp:
            with open(temp.name, "wb") as file_obj:
                file_obj.write(data)

            ret_val = blob.upload_from_filename(
                temp.name, content_type=content_type, client=client
            )

        # Check the response and side-effects.
        self.assertIsNone(ret_val)
        self.assertEqual(blob.metadata, created_json["metadata"])

        # Check the mock.
        stream = self._do_upload_mock_call_helper(blob, client, content_type, len(data))
        self.assertTrue(stream.closed)
        self.assertEqual(stream.mode, "rb")
        self.assertEqual(stream.name, temp.name)

    def test_upload_from_filename_w_custom_timeout(self):
        from google.cloud._testing import _NamedTemporaryFile

        blob = self._make_one("blob-name", bucket=None)
        # Mock low-level upload helper on blob (it is tested elsewhere).
        created_json = {"metadata": {"mint": "ice-cream"}}
        blob._do_upload = mock.Mock(return_value=created_json, spec=[])
        # Make sure `metadata` is empty before the request.
        self.assertIsNone(blob.metadata)

        data = b"soooo much data"
        content_type = u"image/svg+xml"
        client = mock.sentinel.client
        with _NamedTemporaryFile() as temp:
            with open(temp.name, "wb") as file_obj:
                file_obj.write(data)

            blob.upload_from_filename(
                temp.name, content_type=content_type, client=client, timeout=9.58
            )

        # Check the mock.
        self._do_upload_mock_call_helper(
            blob, client, content_type, len(data), timeout=9.58
        )

    def _upload_from_string_helper(self, data, **kwargs):
        from google.cloud._helpers import _to_bytes

        blob = self._make_one("blob-name", bucket=None)

        # Mock low-level upload helper on blob (it is tested elsewhere).
        created_json = {"componentCount": "5"}
        blob._do_upload = mock.Mock(return_value=created_json, spec=[])
        # Make sure `metadata` is empty before the request.
        self.assertIsNone(blob.component_count)

        client = mock.sentinel.client
        ret_val = blob.upload_from_string(data, client=client, **kwargs)

        # Check the response and side-effects.
        self.assertIsNone(ret_val)
        self.assertEqual(blob.component_count, 5)

        # Check the mock.
        payload = _to_bytes(data, encoding="utf-8")
        stream = self._do_upload_mock_call_helper(
            blob,
            client,
            "text/plain",
            len(payload),
            kwargs.get("timeout", self._get_default_timeout()),
        )
        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.getvalue(), payload)

    def test_upload_from_string_w_custom_timeout(self):
        data = b"XB]jb\xb8tad\xe0"
        self._upload_from_string_helper(data, timeout=9.58)

    def test_upload_from_string_w_bytes(self):
        data = b"XB]jb\xb8tad\xe0"
        self._upload_from_string_helper(data)

    def test_upload_from_string_w_text(self):
        data = u"\N{snowman} \N{sailboat}"
        self._upload_from_string_helper(data)

    def _create_resumable_upload_session_helper(
        self, origin=None, side_effect=None, timeout=None
    ):
        bucket = _Bucket(name="alex-trebek")
        blob = self._make_one("blob-name", bucket=bucket)
        chunk_size = 99 * blob._CHUNK_SIZE_MULTIPLE
        blob.chunk_size = chunk_size

        # Create mocks to be checked for doing transport.
        resumable_url = "http://test.invalid?upload_id=clean-up-everybody"
        response_headers = {"location": resumable_url}
        transport = self._mock_transport(http_client.OK, response_headers)
        if side_effect is not None:
            transport.request.side_effect = side_effect

        # Create some mock arguments and call the method under test.
        content_type = u"text/plain"
        size = 10000
        client = mock.Mock(_http=transport, _connection=_Connection, spec=[u"_http"])
        client._connection.API_BASE_URL = "https://storage.googleapis.com"

        if timeout is None:
            expected_timeout = self._get_default_timeout()
            timeout_kwarg = {}
        else:
            expected_timeout = timeout
            timeout_kwarg = {"timeout": timeout}

        new_url = blob.create_resumable_upload_session(
            content_type=content_type,
            size=size,
            origin=origin,
            client=client,
            **timeout_kwarg
        )

        # Check the returned value and (lack of) side-effect.
        self.assertEqual(new_url, resumable_url)
        self.assertEqual(blob.chunk_size, chunk_size)

        # Check the mocks.
        upload_url = (
            "https://storage.googleapis.com/upload/storage/v1"
            + bucket.path
            + "/o?uploadType=resumable"
        )
        payload = b'{"name": "blob-name"}'
        expected_headers = {
            "content-type": "application/json; charset=UTF-8",
            "x-upload-content-length": str(size),
            "x-upload-content-type": content_type,
        }
        if origin is not None:
            expected_headers["Origin"] = origin
        transport.request.assert_called_once_with(
            "POST",
            upload_url,
            data=payload,
            headers=expected_headers,
            timeout=expected_timeout,
        )

    def test_create_resumable_upload_session(self):
        self._create_resumable_upload_session_helper()

    def test_create_resumable_upload_session_with_custom_timeout(self):
        self._create_resumable_upload_session_helper(timeout=9.58)

    def test_create_resumable_upload_session_with_origin(self):
        self._create_resumable_upload_session_helper(origin="http://google.com")

    def test_create_resumable_upload_session_with_failure(self):
        from google.resumable_media import InvalidResponse
        from google.cloud import exceptions

        message = "5-oh-3 woe is me."
        response = self._mock_requests_response(
            status_code=http_client.SERVICE_UNAVAILABLE, headers={}
        )
        side_effect = InvalidResponse(response, message)

        with self.assertRaises(exceptions.ServiceUnavailable) as exc_info:
            self._create_resumable_upload_session_helper(side_effect=side_effect)

        self.assertIn(message, exc_info.exception.message)
        self.assertEqual(exc_info.exception.errors, [])

    def test_get_iam_policy(self):
        from google.cloud.storage.iam import STORAGE_OWNER_ROLE
        from google.cloud.storage.iam import STORAGE_EDITOR_ROLE
        from google.cloud.storage.iam import STORAGE_VIEWER_ROLE
        from google.api_core.iam import Policy

        BLOB_NAME = "blob-name"
        PATH = "/b/name/o/%s" % (BLOB_NAME,)
        ETAG = "DEADBEEF"
        VERSION = 1
        OWNER1 = "user:phred@example.com"
        OWNER2 = "group:cloud-logs@google.com"
        EDITOR1 = "domain:google.com"
        EDITOR2 = "user:phred@example.com"
        VIEWER1 = "serviceAccount:1234-abcdef@service.example.com"
        VIEWER2 = "user:phred@example.com"
        RETURNED = {
            "resourceId": PATH,
            "etag": ETAG,
            "version": VERSION,
            "bindings": [
                {"role": STORAGE_OWNER_ROLE, "members": [OWNER1, OWNER2]},
                {"role": STORAGE_EDITOR_ROLE, "members": [EDITOR1, EDITOR2]},
                {"role": STORAGE_VIEWER_ROLE, "members": [VIEWER1, VIEWER2]},
            ],
        }
        after = ({"status": http_client.OK}, RETURNED)
        EXPECTED = {
            binding["role"]: set(binding["members"]) for binding in RETURNED["bindings"]
        }
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        policy = blob.get_iam_policy(timeout=42)

        self.assertIsInstance(policy, Policy)
        self.assertEqual(policy.etag, RETURNED["etag"])
        self.assertEqual(policy.version, RETURNED["version"])
        self.assertEqual(dict(policy), EXPECTED)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "GET",
                "path": "%s/iam" % (PATH,),
                "query_params": {},
                "_target_object": None,
                "timeout": 42,
                "retry": DEFAULT_RETRY,
            },
        )

    def test_get_iam_policy_w_requested_policy_version(self):
        from google.cloud.storage.iam import STORAGE_OWNER_ROLE

        BLOB_NAME = "blob-name"
        PATH = "/b/name/o/%s" % (BLOB_NAME,)
        ETAG = "DEADBEEF"
        VERSION = 1
        OWNER1 = "user:phred@example.com"
        OWNER2 = "group:cloud-logs@google.com"
        RETURNED = {
            "resourceId": PATH,
            "etag": ETAG,
            "version": VERSION,
            "bindings": [{"role": STORAGE_OWNER_ROLE, "members": [OWNER1, OWNER2]}],
        }
        after = ({"status": http_client.OK}, RETURNED)
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        blob.get_iam_policy(requested_policy_version=3)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "GET",
                "path": "%s/iam" % (PATH,),
                "query_params": {"optionsRequestedPolicyVersion": 3},
                "_target_object": None,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY,
            },
        )

    def test_get_iam_policy_w_user_project(self):
        from google.api_core.iam import Policy

        BLOB_NAME = "blob-name"
        USER_PROJECT = "user-project-123"
        PATH = "/b/name/o/%s" % (BLOB_NAME,)
        ETAG = "DEADBEEF"
        VERSION = 1
        RETURNED = {
            "resourceId": PATH,
            "etag": ETAG,
            "version": VERSION,
            "bindings": [],
        }
        after = ({"status": http_client.OK}, RETURNED)
        EXPECTED = {}
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client, user_project=USER_PROJECT)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        policy = blob.get_iam_policy()

        self.assertIsInstance(policy, Policy)
        self.assertEqual(policy.etag, RETURNED["etag"])
        self.assertEqual(policy.version, RETURNED["version"])
        self.assertEqual(dict(policy), EXPECTED)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "GET",
                "path": "%s/iam" % (PATH,),
                "query_params": {"userProject": USER_PROJECT},
                "_target_object": None,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY,
            },
        )

    def test_set_iam_policy(self):
        import operator
        from google.cloud.storage.iam import STORAGE_OWNER_ROLE
        from google.cloud.storage.iam import STORAGE_EDITOR_ROLE
        from google.cloud.storage.iam import STORAGE_VIEWER_ROLE
        from google.api_core.iam import Policy

        BLOB_NAME = "blob-name"
        PATH = "/b/name/o/%s" % (BLOB_NAME,)
        ETAG = "DEADBEEF"
        VERSION = 1
        OWNER1 = "user:phred@example.com"
        OWNER2 = "group:cloud-logs@google.com"
        EDITOR1 = "domain:google.com"
        EDITOR2 = "user:phred@example.com"
        VIEWER1 = "serviceAccount:1234-abcdef@service.example.com"
        VIEWER2 = "user:phred@example.com"
        BINDINGS = [
            {"role": STORAGE_OWNER_ROLE, "members": [OWNER1, OWNER2]},
            {"role": STORAGE_EDITOR_ROLE, "members": [EDITOR1, EDITOR2]},
            {"role": STORAGE_VIEWER_ROLE, "members": [VIEWER1, VIEWER2]},
        ]
        RETURNED = {"etag": ETAG, "version": VERSION, "bindings": BINDINGS}
        after = ({"status": http_client.OK}, RETURNED)
        policy = Policy()
        for binding in BINDINGS:
            policy[binding["role"]] = binding["members"]

        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        returned = blob.set_iam_policy(policy, timeout=42)

        self.assertEqual(returned.etag, ETAG)
        self.assertEqual(returned.version, VERSION)
        self.assertEqual(dict(returned), dict(policy))

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "PUT")
        self.assertEqual(kw[0]["path"], "%s/iam" % (PATH,))
        self.assertEqual(kw[0]["query_params"], {})
        self.assertEqual(kw[0]["timeout"], 42)
        sent = kw[0]["data"]
        self.assertEqual(sent["resourceId"], PATH)
        self.assertEqual(len(sent["bindings"]), len(BINDINGS))
        key = operator.itemgetter("role")
        for found, expected in zip(
            sorted(sent["bindings"], key=key), sorted(BINDINGS, key=key)
        ):
            self.assertEqual(found["role"], expected["role"])
            self.assertEqual(sorted(found["members"]), sorted(expected["members"]))

    def test_set_iam_policy_w_user_project(self):
        from google.api_core.iam import Policy

        BLOB_NAME = "blob-name"
        USER_PROJECT = "user-project-123"
        PATH = "/b/name/o/%s" % (BLOB_NAME,)
        ETAG = "DEADBEEF"
        VERSION = 1
        BINDINGS = []
        RETURNED = {"etag": ETAG, "version": VERSION, "bindings": BINDINGS}
        after = ({"status": http_client.OK}, RETURNED)
        policy = Policy()

        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client, user_project=USER_PROJECT)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        returned = blob.set_iam_policy(policy)

        self.assertEqual(returned.etag, ETAG)
        self.assertEqual(returned.version, VERSION)
        self.assertEqual(dict(returned), dict(policy))

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "PUT")
        self.assertEqual(kw[0]["path"], "%s/iam" % (PATH,))
        self.assertEqual(kw[0]["query_params"], {"userProject": USER_PROJECT})
        self.assertEqual(kw[0]["data"], {"resourceId": PATH})

    def test_test_iam_permissions(self):
        from google.cloud.storage.iam import STORAGE_OBJECTS_LIST
        from google.cloud.storage.iam import STORAGE_BUCKETS_GET
        from google.cloud.storage.iam import STORAGE_BUCKETS_UPDATE

        BLOB_NAME = "blob-name"
        PATH = "/b/name/o/%s" % (BLOB_NAME,)
        PERMISSIONS = [
            STORAGE_OBJECTS_LIST,
            STORAGE_BUCKETS_GET,
            STORAGE_BUCKETS_UPDATE,
        ]
        ALLOWED = PERMISSIONS[1:]
        RETURNED = {"permissions": ALLOWED}
        after = ({"status": http_client.OK}, RETURNED)
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        allowed = blob.test_iam_permissions(PERMISSIONS, timeout=42)

        self.assertEqual(allowed, ALLOWED)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "GET")
        self.assertEqual(kw[0]["path"], "%s/iam/testPermissions" % (PATH,))
        self.assertEqual(kw[0]["query_params"], {"permissions": PERMISSIONS})
        self.assertEqual(kw[0]["timeout"], 42)

    def test_test_iam_permissions_w_user_project(self):
        from google.cloud.storage.iam import STORAGE_OBJECTS_LIST
        from google.cloud.storage.iam import STORAGE_BUCKETS_GET
        from google.cloud.storage.iam import STORAGE_BUCKETS_UPDATE

        BLOB_NAME = "blob-name"
        USER_PROJECT = "user-project-123"
        PATH = "/b/name/o/%s" % (BLOB_NAME,)
        PERMISSIONS = [
            STORAGE_OBJECTS_LIST,
            STORAGE_BUCKETS_GET,
            STORAGE_BUCKETS_UPDATE,
        ]
        ALLOWED = PERMISSIONS[1:]
        RETURNED = {"permissions": ALLOWED}
        after = ({"status": http_client.OK}, RETURNED)
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client, user_project=USER_PROJECT)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        allowed = blob.test_iam_permissions(PERMISSIONS)

        self.assertEqual(allowed, ALLOWED)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "GET")
        self.assertEqual(kw[0]["path"], "%s/iam/testPermissions" % (PATH,))
        self.assertEqual(
            kw[0]["query_params"],
            {"permissions": PERMISSIONS, "userProject": USER_PROJECT},
        )
        self.assertEqual(kw[0]["timeout"], self._get_default_timeout())

    def test_make_public(self):
        from google.cloud.storage.acl import _ACLEntity

        BLOB_NAME = "blob-name"
        permissive = [{"entity": "allUsers", "role": _ACLEntity.READER_ROLE}]
        after = ({"status": http_client.OK}, {"acl": permissive})
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        blob.acl.loaded = True
        blob.make_public()
        self.assertEqual(list(blob.acl), permissive)
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "PATCH")
        self.assertEqual(kw[0]["path"], "/b/name/o/%s" % BLOB_NAME)
        self.assertEqual(kw[0]["data"], {"acl": permissive})
        self.assertEqual(kw[0]["query_params"], {"projection": "full"})

    def test_make_private(self):
        BLOB_NAME = "blob-name"
        no_permissions = []
        after = ({"status": http_client.OK}, {"acl": no_permissions})
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        blob.acl.loaded = True
        blob.make_private()
        self.assertEqual(list(blob.acl), no_permissions)
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "PATCH")
        self.assertEqual(kw[0]["path"], "/b/name/o/%s" % BLOB_NAME)
        self.assertEqual(kw[0]["data"], {"acl": no_permissions})
        self.assertEqual(kw[0]["query_params"], {"projection": "full"})

    def test_compose_wo_content_type_set(self):
        SOURCE_1 = "source-1"
        SOURCE_2 = "source-2"
        DESTINATION = "destination"
        RESOURCE = {}
        after = ({"status": http_client.OK}, RESOURCE)
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        source_1 = self._make_one(SOURCE_1, bucket=bucket)
        source_2 = self._make_one(SOURCE_2, bucket=bucket)
        destination = self._make_one(DESTINATION, bucket=bucket)
        # no destination.content_type set

        destination.compose(sources=[source_1, source_2])

        self.assertIsNone(destination.content_type)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "POST",
                "path": "/b/name/o/%s/compose" % DESTINATION,
                "query_params": {},
                "data": {
                    "sourceObjects": [{"name": source_1.name}, {"name": source_2.name}],
                    "destination": {},
                },
                "_target_object": destination,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
            },
        )

    def test_compose_minimal_w_user_project(self):
        SOURCE_1 = "source-1"
        SOURCE_2 = "source-2"
        DESTINATION = "destination"
        RESOURCE = {"etag": "DEADBEEF"}
        USER_PROJECT = "user-project-123"
        after = ({"status": http_client.OK}, RESOURCE)
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client, user_project=USER_PROJECT)
        source_1 = self._make_one(SOURCE_1, bucket=bucket)
        source_2 = self._make_one(SOURCE_2, bucket=bucket)
        destination = self._make_one(DESTINATION, bucket=bucket)
        destination.content_type = "text/plain"

        destination.compose(sources=[source_1, source_2], timeout=42)

        self.assertEqual(destination.etag, "DEADBEEF")

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "POST",
                "path": "/b/name/o/%s/compose" % DESTINATION,
                "query_params": {"userProject": USER_PROJECT},
                "data": {
                    "sourceObjects": [{"name": source_1.name}, {"name": source_2.name}],
                    "destination": {"contentType": "text/plain"},
                },
                "_target_object": destination,
                "timeout": 42,
                "retry": DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
            },
        )

    def test_compose_w_additional_property_changes(self):
        SOURCE_1 = "source-1"
        SOURCE_2 = "source-2"
        DESTINATION = "destination"
        RESOURCE = {"etag": "DEADBEEF"}
        after = ({"status": http_client.OK}, RESOURCE)
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        source_1 = self._make_one(SOURCE_1, bucket=bucket)
        source_2 = self._make_one(SOURCE_2, bucket=bucket)
        destination = self._make_one(DESTINATION, bucket=bucket)
        destination.content_type = "text/plain"
        destination.content_language = "en-US"
        destination.metadata = {"my-key": "my-value"}

        destination.compose(sources=[source_1, source_2])

        self.assertEqual(destination.etag, "DEADBEEF")

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "POST",
                "path": "/b/name/o/%s/compose" % DESTINATION,
                "query_params": {},
                "data": {
                    "sourceObjects": [{"name": source_1.name}, {"name": source_2.name}],
                    "destination": {
                        "contentType": "text/plain",
                        "contentLanguage": "en-US",
                        "metadata": {"my-key": "my-value"},
                    },
                },
                "_target_object": destination,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
            },
        )

    def test_compose_w_generation_match(self):
        SOURCE_1 = "source-1"
        SOURCE_2 = "source-2"
        DESTINATION = "destination"
        RESOURCE = {}
        GENERATION_NUMBERS = [6, 9]
        METAGENERATION_NUMBERS = [7, 1]

        after = ({"status": http_client.OK}, RESOURCE)
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        source_1 = self._make_one(SOURCE_1, bucket=bucket)
        source_2 = self._make_one(SOURCE_2, bucket=bucket)

        destination = self._make_one(DESTINATION, bucket=bucket)
        destination.compose(
            sources=[source_1, source_2],
            if_generation_match=GENERATION_NUMBERS,
            if_metageneration_match=METAGENERATION_NUMBERS,
        )

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "POST",
                "path": "/b/name/o/%s/compose" % DESTINATION,
                "query_params": {},
                "data": {
                    "sourceObjects": [
                        {
                            "name": source_1.name,
                            "objectPreconditions": {
                                "ifGenerationMatch": GENERATION_NUMBERS[0],
                                "ifMetagenerationMatch": METAGENERATION_NUMBERS[0],
                            },
                        },
                        {
                            "name": source_2.name,
                            "objectPreconditions": {
                                "ifGenerationMatch": GENERATION_NUMBERS[1],
                                "ifMetagenerationMatch": METAGENERATION_NUMBERS[1],
                            },
                        },
                    ],
                    "destination": {},
                },
                "_target_object": destination,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
            },
        )

    def test_compose_w_generation_match_bad_length(self):
        SOURCE_1 = "source-1"
        SOURCE_2 = "source-2"
        DESTINATION = "destination"
        GENERATION_NUMBERS = [6]
        METAGENERATION_NUMBERS = [7]

        after = ({"status": http_client.OK}, {})
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        source_1 = self._make_one(SOURCE_1, bucket=bucket)
        source_2 = self._make_one(SOURCE_2, bucket=bucket)

        destination = self._make_one(DESTINATION, bucket=bucket)

        with self.assertRaises(ValueError):
            destination.compose(
                sources=[source_1, source_2], if_generation_match=GENERATION_NUMBERS
            )
        with self.assertRaises(ValueError):
            destination.compose(
                sources=[source_1, source_2],
                if_metageneration_match=METAGENERATION_NUMBERS,
            )

    def test_compose_w_generation_match_nones(self):
        SOURCE_1 = "source-1"
        SOURCE_2 = "source-2"
        DESTINATION = "destination"
        GENERATION_NUMBERS = [6, None]

        after = ({"status": http_client.OK}, {})
        connection = _Connection(after)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        source_1 = self._make_one(SOURCE_1, bucket=bucket)
        source_2 = self._make_one(SOURCE_2, bucket=bucket)

        destination = self._make_one(DESTINATION, bucket=bucket)
        destination.compose(
            sources=[source_1, source_2], if_generation_match=GENERATION_NUMBERS
        )

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "POST",
                "path": "/b/name/o/%s/compose" % DESTINATION,
                "query_params": {},
                "data": {
                    "sourceObjects": [
                        {
                            "name": source_1.name,
                            "objectPreconditions": {
                                "ifGenerationMatch": GENERATION_NUMBERS[0]
                            },
                        },
                        {"name": source_2.name},
                    ],
                    "destination": {},
                },
                "_target_object": destination,
                "timeout": self._get_default_timeout(),
                "retry": DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
            },
        )

    def test_rewrite_response_without_resource(self):
        SOURCE_BLOB = "source"
        DEST_BLOB = "dest"
        DEST_BUCKET = "other-bucket"
        TOKEN = "TOKEN"
        RESPONSE = {
            "totalBytesRewritten": 33,
            "objectSize": 42,
            "done": False,
            "rewriteToken": TOKEN,
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        source_bucket = _Bucket(client=client)
        source_blob = self._make_one(SOURCE_BLOB, bucket=source_bucket)
        dest_bucket = _Bucket(client=client, name=DEST_BUCKET)
        dest_blob = self._make_one(DEST_BLOB, bucket=dest_bucket)

        token, rewritten, size = dest_blob.rewrite(source_blob)

        self.assertEqual(token, TOKEN)
        self.assertEqual(rewritten, 33)
        self.assertEqual(size, 42)

    def test_rewrite_w_generations(self):
        SOURCE_BLOB = "source"
        SOURCE_GENERATION = 42
        DEST_BLOB = "dest"
        DEST_BUCKET = "other-bucket"
        DEST_GENERATION = 43
        TOKEN = "TOKEN"
        RESPONSE = {
            "totalBytesRewritten": 33,
            "objectSize": 42,
            "done": False,
            "rewriteToken": TOKEN,
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        source_bucket = _Bucket(client=client)
        source_blob = self._make_one(
            SOURCE_BLOB, bucket=source_bucket, generation=SOURCE_GENERATION
        )
        dest_bucket = _Bucket(client=client, name=DEST_BUCKET)
        dest_blob = self._make_one(
            DEST_BLOB, bucket=dest_bucket, generation=DEST_GENERATION
        )

        token, rewritten, size = dest_blob.rewrite(source_blob, timeout=42)

        self.assertEqual(token, TOKEN)
        self.assertEqual(rewritten, 33)
        self.assertEqual(size, 42)

        (kw,) = connection._requested
        self.assertEqual(kw["method"], "POST")
        self.assertEqual(
            kw["path"],
            "/b/%s/o/%s/rewriteTo/b/%s/o/%s"
            % (
                (source_bucket.name, source_blob.name, dest_bucket.name, dest_blob.name)
            ),
        )
        self.assertEqual(kw["query_params"], {"sourceGeneration": SOURCE_GENERATION})
        self.assertEqual(kw["timeout"], 42)

    def test_rewrite_w_generation_match(self):
        SOURCE_BLOB = "source"
        SOURCE_GENERATION_NUMBER = 42
        DEST_BLOB = "dest"
        DEST_BUCKET = "other-bucket"
        DEST_GENERATION_NUMBER = 16
        TOKEN = "TOKEN"
        RESPONSE = {
            "totalBytesRewritten": 33,
            "objectSize": 42,
            "done": False,
            "rewriteToken": TOKEN,
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        source_bucket = _Bucket(client=client)
        source_blob = self._make_one(
            SOURCE_BLOB, bucket=source_bucket, generation=SOURCE_GENERATION_NUMBER
        )
        dest_bucket = _Bucket(client=client, name=DEST_BUCKET)
        dest_blob = self._make_one(
            DEST_BLOB, bucket=dest_bucket, generation=DEST_GENERATION_NUMBER
        )
        token, rewritten, size = dest_blob.rewrite(
            source_blob,
            timeout=42,
            if_generation_match=dest_blob.generation,
            if_source_generation_match=source_blob.generation,
        )
        (kw,) = connection._requested
        self.assertEqual(kw["method"], "POST")
        self.assertEqual(
            kw["path"],
            "/b/%s/o/%s/rewriteTo/b/%s/o/%s"
            % (
                (source_bucket.name, source_blob.name, dest_bucket.name, dest_blob.name)
            ),
        )
        self.assertEqual(
            kw["query_params"],
            {
                "ifSourceGenerationMatch": SOURCE_GENERATION_NUMBER,
                "ifGenerationMatch": DEST_GENERATION_NUMBER,
                "sourceGeneration": SOURCE_GENERATION_NUMBER,
            },
        )
        self.assertEqual(kw["timeout"], 42)

    def test_rewrite_other_bucket_other_name_no_encryption_partial(self):
        SOURCE_BLOB = "source"
        DEST_BLOB = "dest"
        DEST_BUCKET = "other-bucket"
        TOKEN = "TOKEN"
        RESPONSE = {
            "totalBytesRewritten": 33,
            "objectSize": 42,
            "done": False,
            "rewriteToken": TOKEN,
            "resource": {"etag": "DEADBEEF"},
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        source_bucket = _Bucket(client=client)
        source_blob = self._make_one(SOURCE_BLOB, bucket=source_bucket)
        dest_bucket = _Bucket(client=client, name=DEST_BUCKET)
        dest_blob = self._make_one(DEST_BLOB, bucket=dest_bucket)

        token, rewritten, size = dest_blob.rewrite(source_blob)

        self.assertEqual(token, TOKEN)
        self.assertEqual(rewritten, 33)
        self.assertEqual(size, 42)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "POST")
        PATH = "/b/name/o/%s/rewriteTo/b/%s/o/%s" % (
            SOURCE_BLOB,
            DEST_BUCKET,
            DEST_BLOB,
        )
        self.assertEqual(kw[0]["path"], PATH)
        self.assertEqual(kw[0]["query_params"], {})
        SENT = {}
        self.assertEqual(kw[0]["data"], SENT)
        self.assertEqual(kw[0]["timeout"], self._get_default_timeout())

        headers = {key.title(): str(value) for key, value in kw[0]["headers"].items()}
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Algorithm", headers)
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Key", headers)
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Key-Sha256", headers)
        self.assertNotIn("X-Goog-Encryption-Algorithm", headers)
        self.assertNotIn("X-Goog-Encryption-Key", headers)
        self.assertNotIn("X-Goog-Encryption-Key-Sha256", headers)

    def test_rewrite_same_name_no_old_key_new_key_done_w_user_project(self):
        KEY = b"01234567890123456789012345678901"  # 32 bytes
        KEY_B64 = base64.b64encode(KEY).rstrip().decode("ascii")
        KEY_HASH = hashlib.sha256(KEY).digest()
        KEY_HASH_B64 = base64.b64encode(KEY_HASH).rstrip().decode("ascii")
        BLOB_NAME = "blob"
        USER_PROJECT = "user-project-123"
        RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 42,
            "done": True,
            "resource": {"etag": "DEADBEEF"},
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        bucket = _Bucket(client=client, user_project=USER_PROJECT)
        plain = self._make_one(BLOB_NAME, bucket=bucket)
        encrypted = self._make_one(BLOB_NAME, bucket=bucket, encryption_key=KEY)

        token, rewritten, size = encrypted.rewrite(plain)

        self.assertIsNone(token)
        self.assertEqual(rewritten, 42)
        self.assertEqual(size, 42)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "POST")
        PATH = "/b/name/o/%s/rewriteTo/b/name/o/%s" % (BLOB_NAME, BLOB_NAME)
        self.assertEqual(kw[0]["path"], PATH)
        self.assertEqual(kw[0]["query_params"], {"userProject": USER_PROJECT})
        SENT = {}
        self.assertEqual(kw[0]["data"], SENT)
        self.assertEqual(kw[0]["timeout"], self._get_default_timeout())

        headers = {key.title(): str(value) for key, value in kw[0]["headers"].items()}
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Algorithm", headers)
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Key", headers)
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Key-Sha256", headers)
        self.assertEqual(headers["X-Goog-Encryption-Algorithm"], "AES256")
        self.assertEqual(headers["X-Goog-Encryption-Key"], KEY_B64)
        self.assertEqual(headers["X-Goog-Encryption-Key-Sha256"], KEY_HASH_B64)

    def test_rewrite_same_name_no_key_new_key_w_token(self):
        SOURCE_KEY = b"01234567890123456789012345678901"  # 32 bytes
        SOURCE_KEY_B64 = base64.b64encode(SOURCE_KEY).rstrip().decode("ascii")
        SOURCE_KEY_HASH = hashlib.sha256(SOURCE_KEY).digest()
        SOURCE_KEY_HASH_B64 = base64.b64encode(SOURCE_KEY_HASH).rstrip().decode("ascii")
        DEST_KEY = b"90123456789012345678901234567890"  # 32 bytes
        DEST_KEY_B64 = base64.b64encode(DEST_KEY).rstrip().decode("ascii")
        DEST_KEY_HASH = hashlib.sha256(DEST_KEY).digest()
        DEST_KEY_HASH_B64 = base64.b64encode(DEST_KEY_HASH).rstrip().decode("ascii")
        BLOB_NAME = "blob"
        TOKEN = "TOKEN"
        RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 42,
            "done": True,
            "resource": {"etag": "DEADBEEF"},
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        source = self._make_one(BLOB_NAME, bucket=bucket, encryption_key=SOURCE_KEY)
        dest = self._make_one(BLOB_NAME, bucket=bucket, encryption_key=DEST_KEY)

        token, rewritten, size = dest.rewrite(source, token=TOKEN)

        self.assertIsNone(token)
        self.assertEqual(rewritten, 42)
        self.assertEqual(size, 42)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "POST")
        PATH = "/b/name/o/%s/rewriteTo/b/name/o/%s" % (BLOB_NAME, BLOB_NAME)
        self.assertEqual(kw[0]["path"], PATH)
        self.assertEqual(kw[0]["query_params"], {"rewriteToken": TOKEN})
        SENT = {}
        self.assertEqual(kw[0]["data"], SENT)
        self.assertEqual(kw[0]["timeout"], self._get_default_timeout())

        headers = {key.title(): str(value) for key, value in kw[0]["headers"].items()}
        self.assertEqual(headers["X-Goog-Copy-Source-Encryption-Algorithm"], "AES256")
        self.assertEqual(headers["X-Goog-Copy-Source-Encryption-Key"], SOURCE_KEY_B64)
        self.assertEqual(
            headers["X-Goog-Copy-Source-Encryption-Key-Sha256"], SOURCE_KEY_HASH_B64
        )
        self.assertEqual(headers["X-Goog-Encryption-Algorithm"], "AES256")
        self.assertEqual(headers["X-Goog-Encryption-Key"], DEST_KEY_B64)
        self.assertEqual(headers["X-Goog-Encryption-Key-Sha256"], DEST_KEY_HASH_B64)

    def test_rewrite_same_name_w_old_key_new_kms_key(self):
        SOURCE_KEY = b"01234567890123456789012345678901"  # 32 bytes
        SOURCE_KEY_B64 = base64.b64encode(SOURCE_KEY).rstrip().decode("ascii")
        SOURCE_KEY_HASH = hashlib.sha256(SOURCE_KEY).digest()
        SOURCE_KEY_HASH_B64 = base64.b64encode(SOURCE_KEY_HASH).rstrip().decode("ascii")
        DEST_KMS_RESOURCE = (
            "projects/test-project-123/"
            "locations/us/"
            "keyRings/test-ring/"
            "cryptoKeys/test-key"
        )
        BLOB_NAME = "blob"
        RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 42,
            "done": True,
            "resource": {"etag": "DEADBEEF"},
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        source = self._make_one(BLOB_NAME, bucket=bucket, encryption_key=SOURCE_KEY)
        dest = self._make_one(BLOB_NAME, bucket=bucket, kms_key_name=DEST_KMS_RESOURCE)

        token, rewritten, size = dest.rewrite(source)

        self.assertIsNone(token)
        self.assertEqual(rewritten, 42)
        self.assertEqual(size, 42)

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "POST")
        PATH = "/b/name/o/%s/rewriteTo/b/name/o/%s" % (BLOB_NAME, BLOB_NAME)
        self.assertEqual(kw[0]["path"], PATH)
        self.assertEqual(
            kw[0]["query_params"], {"destinationKmsKeyName": DEST_KMS_RESOURCE}
        )
        self.assertEqual(kw[0]["timeout"], self._get_default_timeout())
        SENT = {"kmsKeyName": DEST_KMS_RESOURCE}
        self.assertEqual(kw[0]["data"], SENT)

        headers = {key.title(): str(value) for key, value in kw[0]["headers"].items()}
        self.assertEqual(headers["X-Goog-Copy-Source-Encryption-Algorithm"], "AES256")
        self.assertEqual(headers["X-Goog-Copy-Source-Encryption-Key"], SOURCE_KEY_B64)
        self.assertEqual(
            headers["X-Goog-Copy-Source-Encryption-Key-Sha256"], SOURCE_KEY_HASH_B64
        )

    def test_update_storage_class_invalid(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        with self.assertRaises(ValueError):
            blob.update_storage_class(u"BOGUS")

    def test_update_storage_class_large_file(self):
        BLOB_NAME = "blob-name"
        STORAGE_CLASS = u"NEARLINE"
        TOKEN = "TOKEN"
        INCOMPLETE_RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 84,
            "done": False,
            "rewriteToken": TOKEN,
            "resource": {"storageClass": STORAGE_CLASS},
        }
        COMPLETE_RESPONSE = {
            "totalBytesRewritten": 84,
            "objectSize": 84,
            "done": True,
            "resource": {"storageClass": STORAGE_CLASS},
        }
        response_1 = ({"status": http_client.OK}, INCOMPLETE_RESPONSE)
        response_2 = ({"status": http_client.OK}, COMPLETE_RESPONSE)
        connection = _Connection(response_1, response_2)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        blob.update_storage_class("NEARLINE")

        self.assertEqual(blob.storage_class, "NEARLINE")

    def test_update_storage_class_with_custom_timeout(self):
        BLOB_NAME = "blob-name"
        STORAGE_CLASS = u"NEARLINE"
        TOKEN = "TOKEN"
        INCOMPLETE_RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 84,
            "done": False,
            "rewriteToken": TOKEN,
            "resource": {"storageClass": STORAGE_CLASS},
        }
        COMPLETE_RESPONSE = {
            "totalBytesRewritten": 84,
            "objectSize": 84,
            "done": True,
            "resource": {"storageClass": STORAGE_CLASS},
        }
        response_1 = ({"status": http_client.OK}, INCOMPLETE_RESPONSE)
        response_2 = ({"status": http_client.OK}, COMPLETE_RESPONSE)
        connection = _Connection(response_1, response_2)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        blob.update_storage_class("NEARLINE", timeout=9.58)

        self.assertEqual(blob.storage_class, "NEARLINE")

        kw = connection._requested
        self.assertEqual(len(kw), 2)

        for kw_item in kw:
            self.assertIn("timeout", kw_item)
            self.assertEqual(kw_item["timeout"], 9.58)

    def test_update_storage_class_wo_encryption_key(self):
        BLOB_NAME = "blob-name"
        STORAGE_CLASS = u"NEARLINE"
        RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 42,
            "done": True,
            "resource": {"storageClass": STORAGE_CLASS},
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        blob.update_storage_class("NEARLINE")

        self.assertEqual(blob.storage_class, "NEARLINE")

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "POST")
        PATH = "/b/name/o/%s/rewriteTo/b/name/o/%s" % (BLOB_NAME, BLOB_NAME)
        self.assertEqual(kw[0]["path"], PATH)
        self.assertEqual(kw[0]["query_params"], {})
        SENT = {"storageClass": STORAGE_CLASS}
        self.assertEqual(kw[0]["data"], SENT)

        headers = {key.title(): str(value) for key, value in kw[0]["headers"].items()}
        # Blob has no key, and therefore the relevant headers are not sent.
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Algorithm", headers)
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Key", headers)
        self.assertNotIn("X-Goog-Copy-Source-Encryption-Key-Sha256", headers)
        self.assertNotIn("X-Goog-Encryption-Algorithm", headers)
        self.assertNotIn("X-Goog-Encryption-Key", headers)
        self.assertNotIn("X-Goog-Encryption-Key-Sha256", headers)

    def test_update_storage_class_w_encryption_key_w_user_project(self):
        BLOB_NAME = "blob-name"
        BLOB_KEY = b"01234567890123456789012345678901"  # 32 bytes
        BLOB_KEY_B64 = base64.b64encode(BLOB_KEY).rstrip().decode("ascii")
        BLOB_KEY_HASH = hashlib.sha256(BLOB_KEY).digest()
        BLOB_KEY_HASH_B64 = base64.b64encode(BLOB_KEY_HASH).rstrip().decode("ascii")
        STORAGE_CLASS = u"NEARLINE"
        USER_PROJECT = "user-project-123"
        RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 42,
            "done": True,
            "resource": {"storageClass": STORAGE_CLASS},
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        bucket = _Bucket(client=client, user_project=USER_PROJECT)
        blob = self._make_one(BLOB_NAME, bucket=bucket, encryption_key=BLOB_KEY)

        blob.update_storage_class("NEARLINE")

        self.assertEqual(blob.storage_class, "NEARLINE")

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "POST")
        PATH = "/b/name/o/%s/rewriteTo/b/name/o/%s" % (BLOB_NAME, BLOB_NAME)
        self.assertEqual(kw[0]["path"], PATH)
        self.assertEqual(kw[0]["query_params"], {"userProject": USER_PROJECT})
        SENT = {"storageClass": STORAGE_CLASS}
        self.assertEqual(kw[0]["data"], SENT)

        headers = {key.title(): str(value) for key, value in kw[0]["headers"].items()}
        # Blob has key, and therefore the relevant headers are sent.
        self.assertEqual(headers["X-Goog-Copy-Source-Encryption-Algorithm"], "AES256")
        self.assertEqual(headers["X-Goog-Copy-Source-Encryption-Key"], BLOB_KEY_B64)
        self.assertEqual(
            headers["X-Goog-Copy-Source-Encryption-Key-Sha256"], BLOB_KEY_HASH_B64
        )
        self.assertEqual(headers["X-Goog-Encryption-Algorithm"], "AES256")
        self.assertEqual(headers["X-Goog-Encryption-Key"], BLOB_KEY_B64)
        self.assertEqual(headers["X-Goog-Encryption-Key-Sha256"], BLOB_KEY_HASH_B64)

    def test_update_storage_class_w_generation_match(self):
        BLOB_NAME = "blob-name"
        STORAGE_CLASS = u"NEARLINE"
        GENERATION_NUMBER = 6
        SOURCE_GENERATION_NUMBER = 9
        RESPONSE = {
            "totalBytesRewritten": 42,
            "objectSize": 42,
            "done": True,
            "resource": {"storageClass": STORAGE_CLASS},
        }
        response = ({"status": http_client.OK}, RESPONSE)
        connection = _Connection(response)
        client = _Client(connection)
        bucket = _Bucket(client=client)
        blob = self._make_one(BLOB_NAME, bucket=bucket)

        blob.update_storage_class(
            "NEARLINE",
            if_generation_match=GENERATION_NUMBER,
            if_source_generation_match=SOURCE_GENERATION_NUMBER,
        )

        self.assertEqual(blob.storage_class, "NEARLINE")

        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "POST")
        PATH = "/b/name/o/%s/rewriteTo/b/name/o/%s" % (BLOB_NAME, BLOB_NAME)
        self.assertEqual(kw[0]["path"], PATH)
        self.assertEqual(
            kw[0]["query_params"],
            {
                "ifGenerationMatch": GENERATION_NUMBER,
                "ifSourceGenerationMatch": SOURCE_GENERATION_NUMBER,
            },
        )
        SENT = {"storageClass": STORAGE_CLASS}
        self.assertEqual(kw[0]["data"], SENT)

    def test_cache_control_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        CACHE_CONTROL = "no-cache"
        properties = {"cacheControl": CACHE_CONTROL}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.cache_control, CACHE_CONTROL)

    def test_cache_control_setter(self):
        BLOB_NAME = "blob-name"
        CACHE_CONTROL = "no-cache"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.cache_control)
        blob.cache_control = CACHE_CONTROL
        self.assertEqual(blob.cache_control, CACHE_CONTROL)

    def test_component_count(self):
        BUCKET = object()
        COMPONENT_COUNT = 42
        blob = self._make_one(
            "blob-name", bucket=BUCKET, properties={"componentCount": COMPONENT_COUNT}
        )
        self.assertEqual(blob.component_count, COMPONENT_COUNT)

    def test_component_count_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.component_count)

    def test_component_count_string_val(self):
        BUCKET = object()
        COMPONENT_COUNT = 42
        blob = self._make_one(
            "blob-name",
            bucket=BUCKET,
            properties={"componentCount": str(COMPONENT_COUNT)},
        )
        self.assertEqual(blob.component_count, COMPONENT_COUNT)

    def test_content_disposition_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        CONTENT_DISPOSITION = "Attachment; filename=example.jpg"
        properties = {"contentDisposition": CONTENT_DISPOSITION}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.content_disposition, CONTENT_DISPOSITION)

    def test_content_disposition_setter(self):
        BLOB_NAME = "blob-name"
        CONTENT_DISPOSITION = "Attachment; filename=example.jpg"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.content_disposition)
        blob.content_disposition = CONTENT_DISPOSITION
        self.assertEqual(blob.content_disposition, CONTENT_DISPOSITION)

    def test_content_encoding_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        CONTENT_ENCODING = "gzip"
        properties = {"contentEncoding": CONTENT_ENCODING}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.content_encoding, CONTENT_ENCODING)

    def test_content_encoding_setter(self):
        BLOB_NAME = "blob-name"
        CONTENT_ENCODING = "gzip"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.content_encoding)
        blob.content_encoding = CONTENT_ENCODING
        self.assertEqual(blob.content_encoding, CONTENT_ENCODING)

    def test_content_language_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        CONTENT_LANGUAGE = "pt-BR"
        properties = {"contentLanguage": CONTENT_LANGUAGE}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.content_language, CONTENT_LANGUAGE)

    def test_content_language_setter(self):
        BLOB_NAME = "blob-name"
        CONTENT_LANGUAGE = "pt-BR"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.content_language)
        blob.content_language = CONTENT_LANGUAGE
        self.assertEqual(blob.content_language, CONTENT_LANGUAGE)

    def test_content_type_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        CONTENT_TYPE = "image/jpeg"
        properties = {"contentType": CONTENT_TYPE}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.content_type, CONTENT_TYPE)

    def test_content_type_setter(self):
        BLOB_NAME = "blob-name"
        CONTENT_TYPE = "image/jpeg"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.content_type)
        blob.content_type = CONTENT_TYPE
        self.assertEqual(blob.content_type, CONTENT_TYPE)

    def test_crc32c_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        CRC32C = "DEADBEEF"
        properties = {"crc32c": CRC32C}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.crc32c, CRC32C)

    def test_crc32c_setter(self):
        BLOB_NAME = "blob-name"
        CRC32C = "DEADBEEF"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.crc32c)
        blob.crc32c = CRC32C
        self.assertEqual(blob.crc32c, CRC32C)

    def test_etag(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        ETAG = "ETAG"
        properties = {"etag": ETAG}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.etag, ETAG)

    def test_event_based_hold_getter_missing(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        properties = {}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertIsNone(blob.event_based_hold)

    def test_event_based_hold_getter_false(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        properties = {"eventBasedHold": False}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertFalse(blob.event_based_hold)

    def test_event_based_hold_getter_true(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        properties = {"eventBasedHold": True}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertTrue(blob.event_based_hold)

    def test_event_based_hold_setter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.event_based_hold)
        blob.event_based_hold = True
        self.assertEqual(blob.event_based_hold, True)

    def test_generation(self):
        BUCKET = object()
        GENERATION = 42
        blob = self._make_one(
            "blob-name", bucket=BUCKET, properties={"generation": GENERATION}
        )
        self.assertEqual(blob.generation, GENERATION)

    def test_generation_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.generation)

    def test_generation_string_val(self):
        BUCKET = object()
        GENERATION = 42
        blob = self._make_one(
            "blob-name", bucket=BUCKET, properties={"generation": str(GENERATION)}
        )
        self.assertEqual(blob.generation, GENERATION)

    def test_id(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        ID = "ID"
        properties = {"id": ID}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.id, ID)

    def test_md5_hash_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        MD5_HASH = "DEADBEEF"
        properties = {"md5Hash": MD5_HASH}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.md5_hash, MD5_HASH)

    def test_md5_hash_setter(self):
        BLOB_NAME = "blob-name"
        MD5_HASH = "DEADBEEF"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.md5_hash)
        blob.md5_hash = MD5_HASH
        self.assertEqual(blob.md5_hash, MD5_HASH)

    def test_media_link(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        MEDIA_LINK = "http://example.com/media/"
        properties = {"mediaLink": MEDIA_LINK}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.media_link, MEDIA_LINK)

    def test_metadata_getter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        METADATA = {"foo": "Foo"}
        properties = {"metadata": METADATA}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.metadata, METADATA)

    def test_metadata_setter(self):
        BLOB_NAME = "blob-name"
        METADATA = {"foo": "Foo"}
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.metadata)
        blob.metadata = METADATA
        self.assertEqual(blob.metadata, METADATA)
        self.assertIn("metadata", blob._changes)

    def test_metadata_setter_w_nan(self):
        BLOB_NAME = "blob-name"
        METADATA = {"foo": float("nan")}
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.metadata)
        blob.metadata = METADATA
        value = blob.metadata["foo"]
        self.assertIsInstance(value, str)
        self.assertIn("metadata", blob._changes)

    def test_metageneration(self):
        BUCKET = object()
        METAGENERATION = 42
        blob = self._make_one(
            "blob-name", bucket=BUCKET, properties={"metageneration": METAGENERATION}
        )
        self.assertEqual(blob.metageneration, METAGENERATION)

    def test_metageneration_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.metageneration)

    def test_metageneration_string_val(self):
        BUCKET = object()
        METAGENERATION = 42
        blob = self._make_one(
            "blob-name",
            bucket=BUCKET,
            properties={"metageneration": str(METAGENERATION)},
        )
        self.assertEqual(blob.metageneration, METAGENERATION)

    def test_owner(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        OWNER = {"entity": "project-owner-12345", "entityId": "23456"}
        properties = {"owner": OWNER}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        owner = blob.owner
        self.assertEqual(owner["entity"], "project-owner-12345")
        self.assertEqual(owner["entityId"], "23456")

    def test_retention_expiration_time(self):
        from google.cloud._helpers import _RFC3339_MICROS
        from google.cloud._helpers import UTC

        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        TIMESTAMP = datetime.datetime(2014, 11, 5, 20, 34, 37, tzinfo=UTC)
        TIME_CREATED = TIMESTAMP.strftime(_RFC3339_MICROS)
        properties = {"retentionExpirationTime": TIME_CREATED}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.retention_expiration_time, TIMESTAMP)

    def test_retention_expiration_time_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.retention_expiration_time)

    def test_self_link(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        SELF_LINK = "http://example.com/self/"
        properties = {"selfLink": SELF_LINK}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.self_link, SELF_LINK)

    def test_size(self):
        BUCKET = object()
        SIZE = 42
        blob = self._make_one("blob-name", bucket=BUCKET, properties={"size": SIZE})
        self.assertEqual(blob.size, SIZE)

    def test_size_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.size)

    def test_size_string_val(self):
        BUCKET = object()
        SIZE = 42
        blob = self._make_one(
            "blob-name", bucket=BUCKET, properties={"size": str(SIZE)}
        )
        self.assertEqual(blob.size, SIZE)

    def test_storage_class_getter(self):
        blob_name = "blob-name"
        bucket = _Bucket()
        storage_class = "COLDLINE"
        properties = {"storageClass": storage_class}
        blob = self._make_one(blob_name, bucket=bucket, properties=properties)
        self.assertEqual(blob.storage_class, storage_class)

    def test_storage_class_setter(self):
        blob_name = "blob-name"
        bucket = _Bucket()
        storage_class = "COLDLINE"
        blob = self._make_one(blob_name, bucket=bucket)
        self.assertIsNone(blob.storage_class)
        blob.storage_class = storage_class
        self.assertEqual(blob.storage_class, storage_class)
        self.assertEqual(blob._properties, {"storageClass": storage_class})

    def test_temporary_hold_getter_missing(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        properties = {}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertIsNone(blob.temporary_hold)

    def test_temporary_hold_getter_false(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        properties = {"temporaryHold": False}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertFalse(blob.temporary_hold)

    def test_temporary_hold_getter_true(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        properties = {"temporaryHold": True}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertTrue(blob.temporary_hold)

    def test_temporary_hold_setter(self):
        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.temporary_hold)
        blob.temporary_hold = True
        self.assertEqual(blob.temporary_hold, True)

    def test_time_deleted(self):
        from google.cloud._helpers import _RFC3339_MICROS
        from google.cloud._helpers import UTC

        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        TIMESTAMP = datetime.datetime(2014, 11, 5, 20, 34, 37, tzinfo=UTC)
        TIME_DELETED = TIMESTAMP.strftime(_RFC3339_MICROS)
        properties = {"timeDeleted": TIME_DELETED}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.time_deleted, TIMESTAMP)

    def test_time_deleted_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.time_deleted)

    def test_time_created(self):
        from google.cloud._helpers import _RFC3339_MICROS
        from google.cloud._helpers import UTC

        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        TIMESTAMP = datetime.datetime(2014, 11, 5, 20, 34, 37, tzinfo=UTC)
        TIME_CREATED = TIMESTAMP.strftime(_RFC3339_MICROS)
        properties = {"timeCreated": TIME_CREATED}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.time_created, TIMESTAMP)

    def test_time_created_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.time_created)

    def test_updated(self):
        from google.cloud._helpers import _RFC3339_MICROS
        from google.cloud._helpers import UTC

        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        TIMESTAMP = datetime.datetime(2014, 11, 5, 20, 34, 37, tzinfo=UTC)
        UPDATED = TIMESTAMP.strftime(_RFC3339_MICROS)
        properties = {"updated": UPDATED}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.updated, TIMESTAMP)

    def test_updated_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.updated)

    def test_custom_time_getter(self):
        from google.cloud._helpers import _RFC3339_MICROS
        from google.cloud._helpers import UTC

        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        TIMESTAMP = datetime.datetime(2014, 11, 5, 20, 34, 37, tzinfo=UTC)
        TIME_CREATED = TIMESTAMP.strftime(_RFC3339_MICROS)
        properties = {"customTime": TIME_CREATED}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.custom_time, TIMESTAMP)

    def test_custom_time_setter(self):
        from google.cloud._helpers import UTC

        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        TIMESTAMP = datetime.datetime(2014, 11, 5, 20, 34, 37, tzinfo=UTC)
        blob = self._make_one(BLOB_NAME, bucket=bucket)
        self.assertIsNone(blob.custom_time)
        blob.custom_time = TIMESTAMP
        self.assertEqual(blob.custom_time, TIMESTAMP)
        self.assertIn("customTime", blob._changes)

    def test_custom_time_setter_none_value(self):
        from google.cloud._helpers import _RFC3339_MICROS
        from google.cloud._helpers import UTC

        BLOB_NAME = "blob-name"
        bucket = _Bucket()
        TIMESTAMP = datetime.datetime(2014, 11, 5, 20, 34, 37, tzinfo=UTC)
        TIME_CREATED = TIMESTAMP.strftime(_RFC3339_MICROS)
        properties = {"customTime": TIME_CREATED}
        blob = self._make_one(BLOB_NAME, bucket=bucket, properties=properties)
        self.assertEqual(blob.custom_time, TIMESTAMP)
        blob.custom_time = None
        self.assertIsNone(blob.custom_time)

    def test_custom_time_unset(self):
        BUCKET = object()
        blob = self._make_one("blob-name", bucket=BUCKET)
        self.assertIsNone(blob.custom_time)

    def test_from_string_w_valid_uri(self):
        from google.cloud.storage.blob import Blob

        connection = _Connection()
        client = _Client(connection)
        uri = "gs://BUCKET_NAME/b"
        blob = Blob.from_string(uri, client)

        self.assertIsInstance(blob, Blob)
        self.assertIs(blob.client, client)
        self.assertEqual(blob.name, "b")
        self.assertEqual(blob.bucket.name, "BUCKET_NAME")

    def test_from_string_w_invalid_uri(self):
        from google.cloud.storage.blob import Blob

        connection = _Connection()
        client = _Client(connection)

        with pytest.raises(ValueError, match="URI scheme must be gs"):
            Blob.from_string("http://bucket_name/b", client)

    def test_from_string_w_domain_name_bucket(self):
        from google.cloud.storage.blob import Blob

        connection = _Connection()
        client = _Client(connection)
        uri = "gs://buckets.example.com/b"
        blob = Blob.from_string(uri, client)

        self.assertIsInstance(blob, Blob)
        self.assertIs(blob.client, client)
        self.assertEqual(blob.name, "b")
        self.assertEqual(blob.bucket.name, "buckets.example.com")


class Test__quote(unittest.TestCase):
    @staticmethod
    def _call_fut(*args, **kw):
        from google.cloud.storage.blob import _quote

        return _quote(*args, **kw)

    def test_bytes(self):
        quoted = self._call_fut(b"\xDE\xAD\xBE\xEF")
        self.assertEqual(quoted, "%DE%AD%BE%EF")

    def test_unicode(self):
        helicopter = u"\U0001f681"
        quoted = self._call_fut(helicopter)
        self.assertEqual(quoted, "%F0%9F%9A%81")

    def test_bad_type(self):
        with self.assertRaises(TypeError):
            self._call_fut(None)

    def test_w_slash_default(self):
        with_slash = "foo/bar/baz"
        quoted = self._call_fut(with_slash)
        self.assertEqual(quoted, "foo%2Fbar%2Fbaz")

    def test_w_slash_w_safe(self):
        with_slash = "foo/bar/baz"
        quoted_safe = self._call_fut(with_slash, safe=b"/")
        self.assertEqual(quoted_safe, with_slash)

    def test_w_tilde(self):
        with_tilde = "bam~qux"
        quoted = self._call_fut(with_tilde, safe=b"~")
        self.assertEqual(quoted, with_tilde)


class Test__maybe_rewind(unittest.TestCase):
    @staticmethod
    def _call_fut(*args, **kwargs):
        from google.cloud.storage.blob import _maybe_rewind

        return _maybe_rewind(*args, **kwargs)

    def test_default(self):
        stream = mock.Mock(spec=[u"seek"])
        ret_val = self._call_fut(stream)
        self.assertIsNone(ret_val)

        stream.seek.assert_not_called()

    def test_do_not_rewind(self):
        stream = mock.Mock(spec=[u"seek"])
        ret_val = self._call_fut(stream, rewind=False)
        self.assertIsNone(ret_val)

        stream.seek.assert_not_called()

    def test_do_rewind(self):
        stream = mock.Mock(spec=[u"seek"])
        ret_val = self._call_fut(stream, rewind=True)
        self.assertIsNone(ret_val)

        stream.seek.assert_called_once_with(0, os.SEEK_SET)


class Test__raise_from_invalid_response(unittest.TestCase):
    @staticmethod
    def _call_fut(error):
        from google.cloud.storage.blob import _raise_from_invalid_response

        return _raise_from_invalid_response(error)

    def _helper(self, message, code=http_client.BAD_REQUEST, reason=None, args=()):
        import requests

        from google.resumable_media import InvalidResponse
        from google.api_core import exceptions

        response = requests.Response()
        response.request = requests.Request("GET", "http://example.com").prepare()
        response._content = reason
        response.status_code = code
        error = InvalidResponse(response, message, *args)

        with self.assertRaises(exceptions.GoogleAPICallError) as exc_info:
            self._call_fut(error)

        return exc_info

    def test_default(self):
        message = "Failure"
        exc_info = self._helper(message)
        expected = "GET http://example.com/: {}".format(message)
        self.assertEqual(exc_info.exception.message, expected)
        self.assertEqual(exc_info.exception.errors, [])

    def test_w_206_and_args(self):
        message = "Failure"
        reason = b"Not available"
        args = ("one", "two")
        exc_info = self._helper(
            message, code=http_client.PARTIAL_CONTENT, reason=reason, args=args
        )
        expected = "GET http://example.com/: {}: {}".format(
            reason.decode("utf-8"), (message,) + args
        )
        self.assertEqual(exc_info.exception.message, expected)
        self.assertEqual(exc_info.exception.errors, [])


class Test__add_query_parameters(unittest.TestCase):
    @staticmethod
    def _call_fut(*args, **kwargs):
        from google.cloud.storage.blob import _add_query_parameters

        return _add_query_parameters(*args, **kwargs)

    def test_w_empty_list(self):
        BASE_URL = "https://test.example.com/base"
        self.assertEqual(self._call_fut(BASE_URL, []), BASE_URL)

    def test_wo_existing_qs(self):
        BASE_URL = "https://test.example.com/base"
        NV_LIST = [("one", "One"), ("two", "Two")]
        expected = "&".join(["{}={}".format(name, value) for name, value in NV_LIST])
        self.assertEqual(
            self._call_fut(BASE_URL, NV_LIST), "{}?{}".format(BASE_URL, expected)
        )

    def test_w_existing_qs(self):
        BASE_URL = "https://test.example.com/base?one=Three"
        NV_LIST = [("one", "One"), ("two", "Two")]
        expected = "&".join(["{}={}".format(name, value) for name, value in NV_LIST])
        self.assertEqual(
            self._call_fut(BASE_URL, NV_LIST), "{}&{}".format(BASE_URL, expected)
        )


class _Connection(object):

    API_BASE_URL = "http://example.com"
    USER_AGENT = "testing 1.2.3"
    credentials = object()

    def __init__(self, *responses):
        self._responses = responses[:]
        self._requested = []
        self._signed = []

    def _respond(self, **kw):
        self._requested.append(kw)
        response, self._responses = self._responses[0], self._responses[1:]
        return response

    def api_request(self, **kw):
        from google.cloud.exceptions import NotFound

        info, content = self._respond(**kw)
        if info.get("status") == http_client.NOT_FOUND:
            raise NotFound(info)
        return content


class _Bucket(object):
    def __init__(self, client=None, name="name", user_project=None):
        if client is None:
            connection = _Connection()
            client = _Client(connection)
        self.client = client
        self._blobs = {}
        self._copied = []
        self._deleted = []
        self.name = name
        self.path = "/b/" + name
        self.user_project = user_project

    def delete_blob(
        self,
        blob_name,
        client=None,
        generation=None,
        timeout=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        retry=DEFAULT_RETRY_IF_GENERATION_SPECIFIED,
    ):
        del self._blobs[blob_name]
        self._deleted.append(
            (
                blob_name,
                client,
                generation,
                timeout,
                if_generation_match,
                if_generation_not_match,
                if_metageneration_match,
                if_metageneration_not_match,
                retry,
            )
        )


class _Client(object):
    def __init__(self, connection):
        self._base_connection = connection

    @property
    def _connection(self):
        return self._base_connection

    @property
    def _credentials(self):
        return self._base_connection.credentials
