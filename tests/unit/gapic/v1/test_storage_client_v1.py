# -*- coding: utf-8 -*-
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests."""

import mock
import pytest

from google.cloud import storage_v1
from google.cloud.storage_v1.proto import storage_pb2
from google.cloud.storage_v1.proto import storage_resources_pb2
from google.iam.v1 import iam_policy_pb2
from google.iam.v1 import policy_pb2
from google.protobuf import empty_pb2


class MultiCallableStub(object):
    """Stub for the grpc.UnaryUnaryMultiCallable interface."""

    def __init__(self, method, channel_stub):
        self.method = method
        self.channel_stub = channel_stub

    def __call__(self, request, timeout=None, metadata=None, credentials=None):
        self.channel_stub.requests.append((self.method, request))

        response = None
        if self.channel_stub.responses:
            response = self.channel_stub.responses.pop()

        if isinstance(response, Exception):
            raise response

        if response:
            return response


class ChannelStub(object):
    """Stub for the grpc.Channel interface."""

    def __init__(self, responses=[]):
        self.responses = responses
        self.requests = []

    def unary_unary(self, method, request_serializer=None, response_deserializer=None):
        return MultiCallableStub(method, self)

    def unary_stream(self, method, request_serializer=None, response_deserializer=None):
        return MultiCallableStub(method, self)

    def stream_unary(self, method, request_serializer=None, response_deserializer=None):
        return MultiCallableStub(method, self)


class CustomException(Exception):
    pass


class TestStorageClient(object):
    def test_delete_bucket_access_control(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        client.delete_bucket_access_control(bucket, entity)

        assert len(channel.requests) == 1
        expected_request = storage_pb2.DeleteBucketAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_delete_bucket_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.delete_bucket_access_control(bucket, entity)

    def test_get_bucket_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.BucketAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        response = client.get_bucket_access_control(bucket, entity)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetBucketAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_bucket_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.get_bucket_access_control(bucket, entity)

    def test_insert_bucket_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        entity = "entity-1298275357"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "entity": entity,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.BucketAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.insert_bucket_access_control(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.InsertBucketAccessControlRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_insert_bucket_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.insert_bucket_access_control(bucket)

    def test_list_bucket_access_controls(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = storage_resources_pb2.ListBucketAccessControlsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.list_bucket_access_controls(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListBucketAccessControlsRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_bucket_access_controls_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.list_bucket_access_controls(bucket)

    def test_update_bucket_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.BucketAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        response = client.update_bucket_access_control(bucket, entity)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.UpdateBucketAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_update_bucket_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.update_bucket_access_control(bucket, entity)

    def test_patch_bucket_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.BucketAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        response = client.patch_bucket_access_control(bucket, entity)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.PatchBucketAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_patch_bucket_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.patch_bucket_access_control(bucket, entity)

    def test_delete_bucket(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        client.delete_bucket(bucket)

        assert len(channel.requests) == 1
        expected_request = storage_pb2.DeleteBucketRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_delete_bucket_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.delete_bucket(bucket)

    def test_get_bucket(self):
        # Setup Expected Response
        id_ = "id3355"
        name = "name3373707"
        project_number = 828084015
        metageneration = 1048558813
        location = "location1901043637"
        storage_class = "storageClass2035762868"
        etag = "etag3123477"
        default_event_based_hold = True
        location_type = "locationType-1796591228"
        expected_response = {
            "id": id_,
            "name": name,
            "project_number": project_number,
            "metageneration": metageneration,
            "location": location,
            "storage_class": storage_class,
            "etag": etag,
            "default_event_based_hold": default_event_based_hold,
            "location_type": location_type,
        }
        expected_response = storage_resources_pb2.Bucket(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.get_bucket(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetBucketRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_bucket_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.get_bucket(bucket)

    def test_insert_bucket(self):
        # Setup Expected Response
        id_ = "id3355"
        name = "name3373707"
        project_number = 828084015
        metageneration = 1048558813
        location = "location1901043637"
        storage_class = "storageClass2035762868"
        etag = "etag3123477"
        default_event_based_hold = True
        location_type = "locationType-1796591228"
        expected_response = {
            "id": id_,
            "name": name,
            "project_number": project_number,
            "metageneration": metageneration,
            "location": location,
            "storage_class": storage_class,
            "etag": etag,
            "default_event_based_hold": default_event_based_hold,
            "location_type": location_type,
        }
        expected_response = storage_resources_pb2.Bucket(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        project = "project-309310695"

        response = client.insert_bucket(project)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.InsertBucketRequest(project=project)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_insert_bucket_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        project = "project-309310695"

        with pytest.raises(CustomException):
            client.insert_bucket(project)

    def test_list_channels(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = storage_resources_pb2.ListChannelsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.list_channels(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListChannelsRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_channels_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.list_channels(bucket)

    def test_list_buckets(self):
        # Setup Expected Response
        next_page_token = "nextPageToken-1530815211"
        expected_response = {"next_page_token": next_page_token}
        expected_response = storage_resources_pb2.ListBucketsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        project = "project-309310695"

        response = client.list_buckets(project)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListBucketsRequest(project=project)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_buckets_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        project = "project-309310695"

        with pytest.raises(CustomException):
            client.list_buckets(project)

    def test_lock_bucket_retention_policy(self):
        # Setup Expected Response
        id_ = "id3355"
        name = "name3373707"
        project_number = 828084015
        metageneration = 1048558813
        location = "location1901043637"
        storage_class = "storageClass2035762868"
        etag = "etag3123477"
        default_event_based_hold = True
        location_type = "locationType-1796591228"
        expected_response = {
            "id": id_,
            "name": name,
            "project_number": project_number,
            "metageneration": metageneration,
            "location": location,
            "storage_class": storage_class,
            "etag": etag,
            "default_event_based_hold": default_event_based_hold,
            "location_type": location_type,
        }
        expected_response = storage_resources_pb2.Bucket(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.lock_bucket_retention_policy(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.LockRetentionPolicyRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_lock_bucket_retention_policy_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.lock_bucket_retention_policy(bucket)

    def test_get_bucket_iam_policy(self):
        # Setup Expected Response
        version = 351608024
        etag = b"etag3123477"
        expected_response = {"version": version, "etag": etag}
        expected_response = policy_pb2.Policy(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.get_bucket_iam_policy()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetIamPolicyRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_bucket_iam_policy_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.get_bucket_iam_policy()

    def test_set_bucket_iam_policy(self):
        # Setup Expected Response
        version = 351608024
        etag = b"etag3123477"
        expected_response = {"version": version, "etag": etag}
        expected_response = policy_pb2.Policy(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.set_bucket_iam_policy()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.SetIamPolicyRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_set_bucket_iam_policy_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.set_bucket_iam_policy()

    def test_test_bucket_iam_permissions(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = iam_policy_pb2.TestIamPermissionsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.test_bucket_iam_permissions()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.TestIamPermissionsRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_test_bucket_iam_permissions_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.test_bucket_iam_permissions()

    def test_patch_bucket(self):
        # Setup Expected Response
        id_ = "id3355"
        name = "name3373707"
        project_number = 828084015
        metageneration = 1048558813
        location = "location1901043637"
        storage_class = "storageClass2035762868"
        etag = "etag3123477"
        default_event_based_hold = True
        location_type = "locationType-1796591228"
        expected_response = {
            "id": id_,
            "name": name,
            "project_number": project_number,
            "metageneration": metageneration,
            "location": location,
            "storage_class": storage_class,
            "etag": etag,
            "default_event_based_hold": default_event_based_hold,
            "location_type": location_type,
        }
        expected_response = storage_resources_pb2.Bucket(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.patch_bucket(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.PatchBucketRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_patch_bucket_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.patch_bucket(bucket)

    def test_update_bucket(self):
        # Setup Expected Response
        id_ = "id3355"
        name = "name3373707"
        project_number = 828084015
        metageneration = 1048558813
        location = "location1901043637"
        storage_class = "storageClass2035762868"
        etag = "etag3123477"
        default_event_based_hold = True
        location_type = "locationType-1796591228"
        expected_response = {
            "id": id_,
            "name": name,
            "project_number": project_number,
            "metageneration": metageneration,
            "location": location,
            "storage_class": storage_class,
            "etag": etag,
            "default_event_based_hold": default_event_based_hold,
            "location_type": location_type,
        }
        expected_response = storage_resources_pb2.Bucket(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.update_bucket(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.UpdateBucketRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_update_bucket_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.update_bucket(bucket)

    def test_stop_channel(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        client.stop_channel()

        assert len(channel.requests) == 1
        expected_request = storage_pb2.StopChannelRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_stop_channel_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.stop_channel()

    def test_delete_default_object_access_control(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        client.delete_default_object_access_control(bucket, entity)

        assert len(channel.requests) == 1
        expected_request = storage_pb2.DeleteDefaultObjectAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_delete_default_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.delete_default_object_access_control(bucket, entity)

    def test_get_default_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_ = "object-1023368385"
        generation = 305703192
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_,
            "generation": generation,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        response = client.get_default_object_access_control(bucket, entity)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetDefaultObjectAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_default_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.get_default_object_access_control(bucket, entity)

    def test_insert_default_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_ = "object-1023368385"
        generation = 305703192
        entity = "entity-1298275357"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_,
            "generation": generation,
            "entity": entity,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.insert_default_object_access_control(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.InsertDefaultObjectAccessControlRequest(
            bucket=bucket
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_insert_default_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.insert_default_object_access_control(bucket)

    def test_list_default_object_access_controls(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = storage_resources_pb2.ListObjectAccessControlsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.list_default_object_access_controls(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListDefaultObjectAccessControlsRequest(
            bucket=bucket
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_default_object_access_controls_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.list_default_object_access_controls(bucket)

    def test_patch_default_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_ = "object-1023368385"
        generation = 305703192
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_,
            "generation": generation,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        response = client.patch_default_object_access_control(bucket, entity)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.PatchDefaultObjectAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_patch_default_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.patch_default_object_access_control(bucket, entity)

    def test_update_default_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_ = "object-1023368385"
        generation = 305703192
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_,
            "generation": generation,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        response = client.update_default_object_access_control(bucket, entity)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.UpdateDefaultObjectAccessControlRequest(
            bucket=bucket, entity=entity
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_update_default_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"

        with pytest.raises(CustomException):
            client.update_default_object_access_control(bucket, entity)

    def test_delete_notification(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        notification = "notification595233003"

        client.delete_notification(bucket, notification)

        assert len(channel.requests) == 1
        expected_request = storage_pb2.DeleteNotificationRequest(
            bucket=bucket, notification=notification
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_delete_notification_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        notification = "notification595233003"

        with pytest.raises(CustomException):
            client.delete_notification(bucket, notification)

    def test_get_notification(self):
        # Setup Expected Response
        topic = "topic110546223"
        etag = "etag3123477"
        object_name_prefix = "objectNamePrefix1265003974"
        payload_format = "payloadFormat-1481910328"
        id_ = "id3355"
        expected_response = {
            "topic": topic,
            "etag": etag,
            "object_name_prefix": object_name_prefix,
            "payload_format": payload_format,
            "id": id_,
        }
        expected_response = storage_resources_pb2.Notification(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        notification = "notification595233003"

        response = client.get_notification(bucket, notification)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetNotificationRequest(
            bucket=bucket, notification=notification
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_notification_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        notification = "notification595233003"

        with pytest.raises(CustomException):
            client.get_notification(bucket, notification)

    def test_insert_notification(self):
        # Setup Expected Response
        topic = "topic110546223"
        etag = "etag3123477"
        object_name_prefix = "objectNamePrefix1265003974"
        payload_format = "payloadFormat-1481910328"
        id_ = "id3355"
        expected_response = {
            "topic": topic,
            "etag": etag,
            "object_name_prefix": object_name_prefix,
            "payload_format": payload_format,
            "id": id_,
        }
        expected_response = storage_resources_pb2.Notification(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.insert_notification(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.InsertNotificationRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_insert_notification_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.insert_notification(bucket)

    def test_list_notifications(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = storage_resources_pb2.ListNotificationsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.list_notifications(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListNotificationsRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_notifications_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.list_notifications(bucket)

    def test_delete_object_access_control(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        client.delete_object_access_control(bucket, entity, object_)

        assert len(channel.requests) == 1
        expected_request = storage_pb2.DeleteObjectAccessControlRequest(
            bucket=bucket, entity=entity, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_delete_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.delete_object_access_control(bucket, entity, object_)

    def test_get_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_2 = "object290495794"
        generation = 305703192
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_2,
            "generation": generation,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        response = client.get_object_access_control(bucket, entity, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetObjectAccessControlRequest(
            bucket=bucket, entity=entity, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.get_object_access_control(bucket, entity, object_)

    def test_insert_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_2 = "object290495794"
        generation = 305703192
        entity = "entity-1298275357"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_2,
            "generation": generation,
            "entity": entity,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        response = client.insert_object_access_control(bucket, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.InsertObjectAccessControlRequest(
            bucket=bucket, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_insert_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.insert_object_access_control(bucket, object_)

    def test_list_object_access_controls(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = storage_resources_pb2.ListObjectAccessControlsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        response = client.list_object_access_controls(bucket, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListObjectAccessControlsRequest(
            bucket=bucket, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_object_access_controls_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.list_object_access_controls(bucket, object_)

    def test_patch_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_2 = "object290495794"
        generation = 305703192
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_2,
            "generation": generation,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        response = client.patch_object_access_control(bucket, entity, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.PatchObjectAccessControlRequest(
            bucket=bucket, entity=entity, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_patch_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.patch_object_access_control(bucket, entity, object_)

    def test_update_object_access_control(self):
        # Setup Expected Response
        role = "role3506294"
        etag = "etag3123477"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        object_2 = "object290495794"
        generation = 305703192
        entity_2 = "entity2-2102099242"
        entity_id = "entityId-740565257"
        email = "email96619420"
        domain = "domain-1326197564"
        expected_response = {
            "role": role,
            "etag": etag,
            "id": id_,
            "bucket": bucket_2,
            "object": object_2,
            "generation": generation,
            "entity": entity_2,
            "entity_id": entity_id,
            "email": email,
            "domain": domain,
        }
        expected_response = storage_resources_pb2.ObjectAccessControl(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        response = client.update_object_access_control(bucket, entity, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.UpdateObjectAccessControlRequest(
            bucket=bucket, entity=entity, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_update_object_access_control_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        entity = "entity-1298275357"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.update_object_access_control(bucket, entity, object_)

    def test_compose_object(self):
        # Setup Expected Response
        content_encoding = "contentEncoding1916674649"
        content_disposition = "contentDisposition891901169"
        cache_control = "cacheControl1032395168"
        content_language = "contentLanguage-1408137122"
        metageneration = 1048558813
        content_type = "contentType831846208"
        size = 3530753
        component_count = 485073075
        md5_hash = "md5Hash1152095023"
        etag = "etag3123477"
        storage_class = "storageClass2035762868"
        kms_key_name = "kmsKeyName2094986649"
        temporary_hold = False
        name = "name3373707"
        id_ = "id3355"
        bucket = "bucket-1378203158"
        generation = 305703192
        expected_response = {
            "content_encoding": content_encoding,
            "content_disposition": content_disposition,
            "cache_control": cache_control,
            "content_language": content_language,
            "metageneration": metageneration,
            "content_type": content_type,
            "size": size,
            "component_count": component_count,
            "md5_hash": md5_hash,
            "etag": etag,
            "storage_class": storage_class,
            "kms_key_name": kms_key_name,
            "temporary_hold": temporary_hold,
            "name": name,
            "id": id_,
            "bucket": bucket,
            "generation": generation,
        }
        expected_response = storage_resources_pb2.Object(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        destination_bucket = "destinationBucket-1744832709"
        destination_object = "destinationObject-1389997936"

        response = client.compose_object(destination_bucket, destination_object)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ComposeObjectRequest(
            destination_bucket=destination_bucket, destination_object=destination_object
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_compose_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        destination_bucket = "destinationBucket-1744832709"
        destination_object = "destinationObject-1389997936"

        with pytest.raises(CustomException):
            client.compose_object(destination_bucket, destination_object)

    def test_copy_object(self):
        # Setup Expected Response
        content_encoding = "contentEncoding1916674649"
        content_disposition = "contentDisposition891901169"
        cache_control = "cacheControl1032395168"
        content_language = "contentLanguage-1408137122"
        metageneration = 1048558813
        content_type = "contentType831846208"
        size = 3530753
        component_count = 485073075
        md5_hash = "md5Hash1152095023"
        etag = "etag3123477"
        storage_class = "storageClass2035762868"
        kms_key_name = "kmsKeyName2094986649"
        temporary_hold = False
        name = "name3373707"
        id_ = "id3355"
        bucket = "bucket-1378203158"
        generation = 305703192
        expected_response = {
            "content_encoding": content_encoding,
            "content_disposition": content_disposition,
            "cache_control": cache_control,
            "content_language": content_language,
            "metageneration": metageneration,
            "content_type": content_type,
            "size": size,
            "component_count": component_count,
            "md5_hash": md5_hash,
            "etag": etag,
            "storage_class": storage_class,
            "kms_key_name": kms_key_name,
            "temporary_hold": temporary_hold,
            "name": name,
            "id": id_,
            "bucket": bucket,
            "generation": generation,
        }
        expected_response = storage_resources_pb2.Object(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        destination_bucket = "destinationBucket-1744832709"
        destination_object = "destinationObject-1389997936"
        source_bucket = "sourceBucket-239822194"
        source_object = "sourceObject115012579"

        response = client.copy_object(
            destination_bucket, destination_object, source_bucket, source_object
        )
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.CopyObjectRequest(
            destination_bucket=destination_bucket,
            destination_object=destination_object,
            source_bucket=source_bucket,
            source_object=source_object,
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_copy_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        destination_bucket = "destinationBucket-1744832709"
        destination_object = "destinationObject-1389997936"
        source_bucket = "sourceBucket-239822194"
        source_object = "sourceObject115012579"

        with pytest.raises(CustomException):
            client.copy_object(
                destination_bucket, destination_object, source_bucket, source_object
            )

    def test_delete_object(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        client.delete_object(bucket, object_)

        assert len(channel.requests) == 1
        expected_request = storage_pb2.DeleteObjectRequest(
            bucket=bucket, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_delete_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.delete_object(bucket, object_)

    def test_get_object(self):
        # Setup Expected Response
        content_encoding = "contentEncoding1916674649"
        content_disposition = "contentDisposition891901169"
        cache_control = "cacheControl1032395168"
        content_language = "contentLanguage-1408137122"
        metageneration = 1048558813
        content_type = "contentType831846208"
        size = 3530753
        component_count = 485073075
        md5_hash = "md5Hash1152095023"
        etag = "etag3123477"
        storage_class = "storageClass2035762868"
        kms_key_name = "kmsKeyName2094986649"
        temporary_hold = False
        name = "name3373707"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        generation = 305703192
        expected_response = {
            "content_encoding": content_encoding,
            "content_disposition": content_disposition,
            "cache_control": cache_control,
            "content_language": content_language,
            "metageneration": metageneration,
            "content_type": content_type,
            "size": size,
            "component_count": component_count,
            "md5_hash": md5_hash,
            "etag": etag,
            "storage_class": storage_class,
            "kms_key_name": kms_key_name,
            "temporary_hold": temporary_hold,
            "name": name,
            "id": id_,
            "bucket": bucket_2,
            "generation": generation,
        }
        expected_response = storage_resources_pb2.Object(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        response = client.get_object(bucket, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetObjectRequest(bucket=bucket, object=object_)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.get_object(bucket, object_)

    def test_get_object_media(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = storage_pb2.GetObjectMediaResponse(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[iter([expected_response])])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.get_object_media()
        resources = list(response)
        assert len(resources) == 1
        assert expected_response == resources[0]

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetObjectMediaRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_object_media_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.get_object_media()

    def test_insert_object(self):
        # Setup Expected Response
        content_encoding = "contentEncoding1916674649"
        content_disposition = "contentDisposition891901169"
        cache_control = "cacheControl1032395168"
        content_language = "contentLanguage-1408137122"
        metageneration = 1048558813
        content_type = "contentType831846208"
        size = 3530753
        component_count = 485073075
        md5_hash = "md5Hash1152095023"
        etag = "etag3123477"
        storage_class = "storageClass2035762868"
        kms_key_name = "kmsKeyName2094986649"
        temporary_hold = False
        name = "name3373707"
        id_ = "id3355"
        bucket = "bucket-1378203158"
        generation = 305703192
        expected_response = {
            "content_encoding": content_encoding,
            "content_disposition": content_disposition,
            "cache_control": cache_control,
            "content_language": content_language,
            "metageneration": metageneration,
            "content_type": content_type,
            "size": size,
            "component_count": component_count,
            "md5_hash": md5_hash,
            "etag": etag,
            "storage_class": storage_class,
            "kms_key_name": kms_key_name,
            "temporary_hold": temporary_hold,
            "name": name,
            "id": id_,
            "bucket": bucket,
            "generation": generation,
        }
        expected_response = storage_resources_pb2.Object(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        write_offset = 1559543565
        request = {"write_offset": write_offset}
        request = storage_pb2.InsertObjectRequest(**request)
        requests = [request]

        response = client.insert_object(requests)
        assert expected_response == response

        assert len(channel.requests) == 1
        actual_requests = channel.requests[0][1]
        assert len(actual_requests) == 1
        actual_request = list(actual_requests)[0]
        assert request == actual_request

    def test_insert_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        write_offset = 1559543565
        request = {"write_offset": write_offset}

        request = storage_pb2.InsertObjectRequest(**request)
        requests = [request]

        with pytest.raises(CustomException):
            client.insert_object(requests)

    def test_list_objects(self):
        # Setup Expected Response
        next_page_token = "nextPageToken-1530815211"
        expected_response = {"next_page_token": next_page_token}
        expected_response = storage_resources_pb2.ListObjectsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"

        response = client.list_objects(bucket)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListObjectsRequest(bucket=bucket)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_objects_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"

        with pytest.raises(CustomException):
            client.list_objects(bucket)

    def test_rewrite_object(self):
        # Setup Expected Response
        total_bytes_rewritten = 1109205579
        object_size = 1277221631
        done = True
        rewrite_token = "rewriteToken-1475021434"
        expected_response = {
            "total_bytes_rewritten": total_bytes_rewritten,
            "object_size": object_size,
            "done": done,
            "rewrite_token": rewrite_token,
        }
        expected_response = storage_pb2.RewriteResponse(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        destination_bucket = "destinationBucket-1744832709"
        destination_object = "destinationObject-1389997936"
        source_bucket = "sourceBucket-239822194"
        source_object = "sourceObject115012579"

        response = client.rewrite_object(
            destination_bucket, destination_object, source_bucket, source_object
        )
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.RewriteObjectRequest(
            destination_bucket=destination_bucket,
            destination_object=destination_object,
            source_bucket=source_bucket,
            source_object=source_object,
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_rewrite_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        destination_bucket = "destinationBucket-1744832709"
        destination_object = "destinationObject-1389997936"
        source_bucket = "sourceBucket-239822194"
        source_object = "sourceObject115012579"

        with pytest.raises(CustomException):
            client.rewrite_object(
                destination_bucket, destination_object, source_bucket, source_object
            )

    def test_start_resumable_write(self):
        # Setup Expected Response
        upload_id = "uploadId1239095321"
        expected_response = {"upload_id": upload_id}
        expected_response = storage_pb2.StartResumableWriteResponse(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.start_resumable_write()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.StartResumableWriteRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_start_resumable_write_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.start_resumable_write()

    def test_query_write_status(self):
        # Setup Expected Response
        committed_size = 1907158756
        complete = False
        expected_response = {"committed_size": committed_size, "complete": complete}
        expected_response = storage_pb2.QueryWriteStatusResponse(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        upload_id = "uploadId1239095321"

        response = client.query_write_status(upload_id)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.QueryWriteStatusRequest(upload_id=upload_id)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_query_write_status_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        upload_id = "uploadId1239095321"

        with pytest.raises(CustomException):
            client.query_write_status(upload_id)

    def test_patch_object(self):
        # Setup Expected Response
        content_encoding = "contentEncoding1916674649"
        content_disposition = "contentDisposition891901169"
        cache_control = "cacheControl1032395168"
        content_language = "contentLanguage-1408137122"
        metageneration = 1048558813
        content_type = "contentType831846208"
        size = 3530753
        component_count = 485073075
        md5_hash = "md5Hash1152095023"
        etag = "etag3123477"
        storage_class = "storageClass2035762868"
        kms_key_name = "kmsKeyName2094986649"
        temporary_hold = False
        name = "name3373707"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        generation = 305703192
        expected_response = {
            "content_encoding": content_encoding,
            "content_disposition": content_disposition,
            "cache_control": cache_control,
            "content_language": content_language,
            "metageneration": metageneration,
            "content_type": content_type,
            "size": size,
            "component_count": component_count,
            "md5_hash": md5_hash,
            "etag": etag,
            "storage_class": storage_class,
            "kms_key_name": kms_key_name,
            "temporary_hold": temporary_hold,
            "name": name,
            "id": id_,
            "bucket": bucket_2,
            "generation": generation,
        }
        expected_response = storage_resources_pb2.Object(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        response = client.patch_object(bucket, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.PatchObjectRequest(bucket=bucket, object=object_)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_patch_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.patch_object(bucket, object_)

    def test_update_object(self):
        # Setup Expected Response
        content_encoding = "contentEncoding1916674649"
        content_disposition = "contentDisposition891901169"
        cache_control = "cacheControl1032395168"
        content_language = "contentLanguage-1408137122"
        metageneration = 1048558813
        content_type = "contentType831846208"
        size = 3530753
        component_count = 485073075
        md5_hash = "md5Hash1152095023"
        etag = "etag3123477"
        storage_class = "storageClass2035762868"
        kms_key_name = "kmsKeyName2094986649"
        temporary_hold = False
        name = "name3373707"
        id_ = "id3355"
        bucket_2 = "bucket2-1603304675"
        generation = 305703192
        expected_response = {
            "content_encoding": content_encoding,
            "content_disposition": content_disposition,
            "cache_control": cache_control,
            "content_language": content_language,
            "metageneration": metageneration,
            "content_type": content_type,
            "size": size,
            "component_count": component_count,
            "md5_hash": md5_hash,
            "etag": etag,
            "storage_class": storage_class,
            "kms_key_name": kms_key_name,
            "temporary_hold": temporary_hold,
            "name": name,
            "id": id_,
            "bucket": bucket_2,
            "generation": generation,
        }
        expected_response = storage_resources_pb2.Object(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        response = client.update_object(bucket, object_)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.UpdateObjectRequest(
            bucket=bucket, object=object_
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_update_object_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        bucket = "bucket-1378203158"
        object_ = "object-1023368385"

        with pytest.raises(CustomException):
            client.update_object(bucket, object_)

    def test_get_object_iam_policy(self):
        # Setup Expected Response
        version = 351608024
        etag = b"etag3123477"
        expected_response = {"version": version, "etag": etag}
        expected_response = policy_pb2.Policy(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.get_object_iam_policy()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetIamPolicyRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_object_iam_policy_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.get_object_iam_policy()

    def test_set_object_iam_policy(self):
        # Setup Expected Response
        version = 351608024
        etag = b"etag3123477"
        expected_response = {"version": version, "etag": etag}
        expected_response = policy_pb2.Policy(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.set_object_iam_policy()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.SetIamPolicyRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_set_object_iam_policy_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.set_object_iam_policy()

    def test_test_object_iam_permissions(self):
        # Setup Expected Response
        expected_response = {}
        expected_response = iam_policy_pb2.TestIamPermissionsResponse(
            **expected_response
        )

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.test_object_iam_permissions()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.TestIamPermissionsRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_test_object_iam_permissions_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.test_object_iam_permissions()

    def test_watch_all_objects(self):
        # Setup Expected Response
        id_ = "id3355"
        resource_id = "resourceId1234537196"
        resource_uri = "resourceUri-384040517"
        token = "token110541305"
        type_ = "type3575610"
        address = "address-1147692044"
        payload = True
        expected_response = {
            "id": id_,
            "resource_id": resource_id,
            "resource_uri": resource_uri,
            "token": token,
            "type": type_,
            "address": address,
            "payload": payload,
        }
        expected_response = storage_resources_pb2.Channel(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        response = client.watch_all_objects()
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.WatchAllObjectsRequest()
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_watch_all_objects_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        with pytest.raises(CustomException):
            client.watch_all_objects()

    def test_get_service_account(self):
        # Setup Expected Response
        email_address = "emailAddress-769510831"
        expected_response = {"email_address": email_address}
        expected_response = storage_resources_pb2.ServiceAccount(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        project_id = "projectId-1969970175"

        response = client.get_service_account(project_id)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetProjectServiceAccountRequest(
            project_id=project_id
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_service_account_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        project_id = "projectId-1969970175"

        with pytest.raises(CustomException):
            client.get_service_account(project_id)

    def test_create_hmac_key(self):
        # Setup Expected Response
        secret = "secret-906277200"
        expected_response = {"secret": secret}
        expected_response = storage_pb2.CreateHmacKeyResponse(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        project_id = "projectId-1969970175"
        service_account_email = "serviceAccountEmail-1300473088"

        response = client.create_hmac_key(project_id, service_account_email)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.CreateHmacKeyRequest(
            project_id=project_id, service_account_email=service_account_email
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_create_hmac_key_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        project_id = "projectId-1969970175"
        service_account_email = "serviceAccountEmail-1300473088"

        with pytest.raises(CustomException):
            client.create_hmac_key(project_id, service_account_email)

    def test_delete_hmac_key(self):
        channel = ChannelStub()
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        access_id = "accessId-2115038762"
        project_id = "projectId-1969970175"

        client.delete_hmac_key(access_id, project_id)

        assert len(channel.requests) == 1
        expected_request = storage_pb2.DeleteHmacKeyRequest(
            access_id=access_id, project_id=project_id
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_delete_hmac_key_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        access_id = "accessId-2115038762"
        project_id = "projectId-1969970175"

        with pytest.raises(CustomException):
            client.delete_hmac_key(access_id, project_id)

    def test_get_hmac_key(self):
        # Setup Expected Response
        id_ = "id3355"
        access_id_2 = "accessId2-1032716279"
        project_id_2 = "projectId2939242356"
        service_account_email = "serviceAccountEmail-1300473088"
        state = "state109757585"
        etag = "etag3123477"
        expected_response = {
            "id": id_,
            "access_id": access_id_2,
            "project_id": project_id_2,
            "service_account_email": service_account_email,
            "state": state,
            "etag": etag,
        }
        expected_response = storage_resources_pb2.HmacKeyMetadata(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        access_id = "accessId-2115038762"
        project_id = "projectId-1969970175"

        response = client.get_hmac_key(access_id, project_id)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.GetHmacKeyRequest(
            access_id=access_id, project_id=project_id
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_get_hmac_key_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        access_id = "accessId-2115038762"
        project_id = "projectId-1969970175"

        with pytest.raises(CustomException):
            client.get_hmac_key(access_id, project_id)

    def test_list_hmac_keys(self):
        # Setup Expected Response
        next_page_token = "nextPageToken-1530815211"
        expected_response = {"next_page_token": next_page_token}
        expected_response = storage_pb2.ListHmacKeysResponse(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        project_id = "projectId-1969970175"

        response = client.list_hmac_keys(project_id)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.ListHmacKeysRequest(project_id=project_id)
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_list_hmac_keys_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        project_id = "projectId-1969970175"

        with pytest.raises(CustomException):
            client.list_hmac_keys(project_id)

    def test_update_hmac_key(self):
        # Setup Expected Response
        id_ = "id3355"
        access_id_2 = "accessId2-1032716279"
        project_id_2 = "projectId2939242356"
        service_account_email = "serviceAccountEmail-1300473088"
        state = "state109757585"
        etag = "etag3123477"
        expected_response = {
            "id": id_,
            "access_id": access_id_2,
            "project_id": project_id_2,
            "service_account_email": service_account_email,
            "state": state,
            "etag": etag,
        }
        expected_response = storage_resources_pb2.HmacKeyMetadata(**expected_response)

        # Mock the API response
        channel = ChannelStub(responses=[expected_response])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup Request
        access_id = "accessId-2115038762"
        project_id = "projectId-1969970175"
        metadata = {}

        response = client.update_hmac_key(access_id, project_id, metadata)
        assert expected_response == response

        assert len(channel.requests) == 1
        expected_request = storage_pb2.UpdateHmacKeyRequest(
            access_id=access_id, project_id=project_id, metadata=metadata
        )
        actual_request = channel.requests[0][1]
        assert expected_request == actual_request

    def test_update_hmac_key_exception(self):
        # Mock the API response
        channel = ChannelStub(responses=[CustomException()])
        patch = mock.patch("google.api_core.grpc_helpers.create_channel")
        with patch as create_channel:
            create_channel.return_value = channel
            client = storage_v1.StorageClient()

        # Setup request
        access_id = "accessId-2115038762"
        project_id = "projectId-1969970175"
        metadata = {}

        with pytest.raises(CustomException):
            client.update_hmac_key(access_id, project_id, metadata)
