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


import google.api_core.grpc_helpers

from google.cloud.storage_v1.proto import storage_pb2_grpc


class StorageGrpcTransport(object):
    """gRPC transport class providing stubs for
    google.storage.v1 Storage API.

    The transport provides access to the raw gRPC stubs,
    which can be used to take advantage of advanced
    features of gRPC.
    """

    # The scopes needed to make gRPC calls to all of the methods defined
    # in this service.
    _OAUTH_SCOPES = (
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/cloud-platform.read-only",
        "https://www.googleapis.com/auth/devstorage.full_control",
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/devstorage.read_write",
    )

    def __init__(
        self, channel=None, credentials=None, address="storage.googleapis.com:443"
    ):
        """Instantiate the transport class.

        Args:
            channel (grpc.Channel): A ``Channel`` instance through
                which to make calls. This argument is mutually exclusive
                with ``credentials``; providing both will raise an exception.
            credentials (google.auth.credentials.Credentials): The
                authorization credentials to attach to requests. These
                credentials identify this application to the service. If none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            address (str): The address where the service is hosted.
        """
        # If both `channel` and `credentials` are specified, raise an
        # exception (channels come with credentials baked in already).
        if channel is not None and credentials is not None:
            raise ValueError(
                "The `channel` and `credentials` arguments are mutually " "exclusive.",
            )

        # Create the channel.
        if channel is None:
            channel = self.create_channel(
                address=address,
                credentials=credentials,
                options={
                    "grpc.max_send_message_length": -1,
                    "grpc.max_receive_message_length": -1,
                }.items(),
            )

        self._channel = channel

        # gRPC uses objects called "stubs" that are bound to the
        # channel and provide a basic method for each RPC.
        self._stubs = {
            "storage_stub": storage_pb2_grpc.StorageStub(channel),
        }

    @classmethod
    def create_channel(
        cls, address="storage.googleapis.com:443", credentials=None, **kwargs
    ):
        """Create and return a gRPC channel object.

        Args:
            address (str): The host for the channel to use.
            credentials (~.Credentials): The
                authorization credentials to attach to requests. These
                credentials identify this application to the service. If
                none are specified, the client will attempt to ascertain
                the credentials from the environment.
            kwargs (dict): Keyword arguments, which are passed to the
                channel creation.

        Returns:
            grpc.Channel: A gRPC channel object.
        """
        return google.api_core.grpc_helpers.create_channel(
            address, credentials=credentials, scopes=cls._OAUTH_SCOPES, **kwargs
        )

    @property
    def channel(self):
        """The gRPC channel used by the transport.

        Returns:
            grpc.Channel: A gRPC channel object.
        """
        return self._channel

    @property
    def delete_bucket_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.delete_bucket_access_control`.

        Permanently deletes the ACL entry for the specified entity on the specified
        bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].DeleteBucketAccessControl

    @property
    def get_bucket_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.get_bucket_access_control`.

        Returns the ACL entry for the specified entity on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetBucketAccessControl

    @property
    def insert_bucket_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.insert_bucket_access_control`.

        Creates a new ACL entry on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].InsertBucketAccessControl

    @property
    def list_bucket_access_controls(self):
        """Return the gRPC stub for :meth:`StorageClient.list_bucket_access_controls`.

        Retrieves ACL entries on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListBucketAccessControls

    @property
    def update_bucket_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.update_bucket_access_control`.

        Updates an ACL entry on the specified bucket. Equivalent to
        PatchBucketAccessControl, but all unspecified fields will be
        reset to their default values.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].UpdateBucketAccessControl

    @property
    def patch_bucket_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.patch_bucket_access_control`.

        Updates an ACL entry on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].PatchBucketAccessControl

    @property
    def delete_bucket(self):
        """Return the gRPC stub for :meth:`StorageClient.delete_bucket`.

        Permanently deletes an empty bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].DeleteBucket

    @property
    def get_bucket(self):
        """Return the gRPC stub for :meth:`StorageClient.get_bucket`.

        Returns metadata for the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetBucket

    @property
    def insert_bucket(self):
        """Return the gRPC stub for :meth:`StorageClient.insert_bucket`.

        Creates a new bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].InsertBucket

    @property
    def list_channels(self):
        """Return the gRPC stub for :meth:`StorageClient.list_channels`.

        List active object change notification channels for this bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListChannels

    @property
    def list_buckets(self):
        """Return the gRPC stub for :meth:`StorageClient.list_buckets`.

        Retrieves a list of buckets for a given project.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListBuckets

    @property
    def lock_bucket_retention_policy(self):
        """Return the gRPC stub for :meth:`StorageClient.lock_bucket_retention_policy`.

        Locks retention policy on a bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].LockBucketRetentionPolicy

    @property
    def get_bucket_iam_policy(self):
        """Return the gRPC stub for :meth:`StorageClient.get_bucket_iam_policy`.

        Gets the IAM policy for the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetBucketIamPolicy

    @property
    def set_bucket_iam_policy(self):
        """Return the gRPC stub for :meth:`StorageClient.set_bucket_iam_policy`.

        Updates an IAM policy for the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].SetBucketIamPolicy

    @property
    def test_bucket_iam_permissions(self):
        """Return the gRPC stub for :meth:`StorageClient.test_bucket_iam_permissions`.

        Tests a set of permissions on the given bucket to see which, if
        any, are held by the caller.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].TestBucketIamPermissions

    @property
    def patch_bucket(self):
        """Return the gRPC stub for :meth:`StorageClient.patch_bucket`.

        Updates a bucket. Changes to the bucket will be readable immediately after
        writing, but configuration changes may take time to propagate.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].PatchBucket

    @property
    def update_bucket(self):
        """Return the gRPC stub for :meth:`StorageClient.update_bucket`.

        Updates a bucket. Equivalent to PatchBucket, but always replaces all
        mutatable fields of the bucket with new values, reverting all
        unspecified fields to their default values.
        Like PatchBucket, Changes to the bucket will be readable immediately after
        writing, but configuration changes may take time to propagate.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].UpdateBucket

    @property
    def stop_channel(self):
        """Return the gRPC stub for :meth:`StorageClient.stop_channel`.

        Halts "Object Change Notification" push messagages.
        See https://cloud.google.com/storage/docs/object-change-notification
        Note: this is not related to the newer "Notifications" resource, which
        are stopped using DeleteNotification.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].StopChannel

    @property
    def delete_default_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.delete_default_object_access_control`.

        Permanently deletes the default object ACL entry for the specified entity
        on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].DeleteDefaultObjectAccessControl

    @property
    def get_default_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.get_default_object_access_control`.

        Returns the default object ACL entry for the specified entity on the
        specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetDefaultObjectAccessControl

    @property
    def insert_default_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.insert_default_object_access_control`.

        Creates a new default object ACL entry on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].InsertDefaultObjectAccessControl

    @property
    def list_default_object_access_controls(self):
        """Return the gRPC stub for :meth:`StorageClient.list_default_object_access_controls`.

        Retrieves default object ACL entries on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListDefaultObjectAccessControls

    @property
    def patch_default_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.patch_default_object_access_control`.

        Updates a default object ACL entry on the specified bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].PatchDefaultObjectAccessControl

    @property
    def update_default_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.update_default_object_access_control`.

        Updates a default object ACL entry on the specified bucket. Equivalent to
        PatchDefaultObjectAccessControl, but modifies all unspecified fields to
        their default values.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].UpdateDefaultObjectAccessControl

    @property
    def delete_notification(self):
        """Return the gRPC stub for :meth:`StorageClient.delete_notification`.

        Permanently deletes a notification subscription.
        Note: Older, "Object Change Notification" push subscriptions should be
        deleted using StopChannel instead.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].DeleteNotification

    @property
    def get_notification(self):
        """Return the gRPC stub for :meth:`StorageClient.get_notification`.

        View a notification configuration.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetNotification

    @property
    def insert_notification(self):
        """Return the gRPC stub for :meth:`StorageClient.insert_notification`.

        Creates a notification subscription for a given bucket.
        These notifications, when triggered, publish messages to the specified
        Cloud Pub/Sub topics.
        See https://cloud.google.com/storage/docs/pubsub-notifications.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].InsertNotification

    @property
    def list_notifications(self):
        """Return the gRPC stub for :meth:`StorageClient.list_notifications`.

        Retrieves a list of notification subscriptions for a given bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListNotifications

    @property
    def delete_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.delete_object_access_control`.

        Permanently deletes the ACL entry for the specified entity on the specified
        object.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].DeleteObjectAccessControl

    @property
    def get_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.get_object_access_control`.

        Returns the ACL entry for the specified entity on the specified object.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetObjectAccessControl

    @property
    def insert_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.insert_object_access_control`.

        Creates a new ACL entry on the specified object.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].InsertObjectAccessControl

    @property
    def list_object_access_controls(self):
        """Return the gRPC stub for :meth:`StorageClient.list_object_access_controls`.

        Retrieves ACL entries on the specified object.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListObjectAccessControls

    @property
    def patch_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.patch_object_access_control`.

        Patches an ACL entry on the specified object. Patch is similar to
        update, but only applies or appends the specified fields in the
        object_access_control object. Other fields are unaffected.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].PatchObjectAccessControl

    @property
    def update_object_access_control(self):
        """Return the gRPC stub for :meth:`StorageClient.update_object_access_control`.

        Updates an ACL entry on the specified object.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].UpdateObjectAccessControl

    @property
    def compose_object(self):
        """Return the gRPC stub for :meth:`StorageClient.compose_object`.

        Concatenates a list of existing objects into a new object in the same
        bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ComposeObject

    @property
    def copy_object(self):
        """Return the gRPC stub for :meth:`StorageClient.copy_object`.

        Copies a source object to a destination object. Optionally overrides
        metadata.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].CopyObject

    @property
    def delete_object(self):
        """Return the gRPC stub for :meth:`StorageClient.delete_object`.

        Deletes an object and its metadata. Deletions are permanent if
        versioning is not enabled for the bucket, or if the ``generation``
        parameter is used.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].DeleteObject

    @property
    def get_object(self):
        """Return the gRPC stub for :meth:`StorageClient.get_object`.

        Retrieves an object's metadata.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetObject

    @property
    def get_object_media(self):
        """Return the gRPC stub for :meth:`StorageClient.get_object_media`.

        Reads an object's data.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetObjectMedia

    @property
    def insert_object(self):
        """Return the gRPC stub for :meth:`StorageClient.insert_object`.

        Stores a new object and metadata.

        An object can be written either in a single message stream or in a
        resumable sequence of message streams. To write using a single stream,
        the client should include in the first message of the stream an
        ``InsertObjectSpec`` describing the destination bucket, object, and any
        preconditions. Additionally, the final message must set 'finish_write'
        to true, or else it is an error.

        For a resumable write, the client should instead call
        ``StartResumableWrite()`` and provide that method an
        ``InsertObjectSpec.`` They should then attach the returned ``upload_id``
        to the first message of each following call to ``Insert``. If there is
        an error or the connection is broken during the resumable ``Insert()``,
        the client should check the status of the ``Insert()`` by calling
        ``QueryWriteStatus()`` and continue writing from the returned
        ``committed_size``. This may be less than the amount of data the client
        previously sent.

        The service will not view the object as complete until the client has
        sent an ``Insert`` with ``finish_write`` set to ``true``. Sending any
        requests on a stream after sending a request with ``finish_write`` set
        to ``true`` will cause an error. The client **should** check the
        ``Object`` it receives to determine how much data the service was able
        to commit and whether the service views the object as complete.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].InsertObject

    @property
    def list_objects(self):
        """Return the gRPC stub for :meth:`StorageClient.list_objects`.

        Retrieves a list of objects matching the criteria.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListObjects

    @property
    def rewrite_object(self):
        """Return the gRPC stub for :meth:`StorageClient.rewrite_object`.

        Rewrites a source object to a destination object. Optionally overrides
        metadata.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].RewriteObject

    @property
    def start_resumable_write(self):
        """Return the gRPC stub for :meth:`StorageClient.start_resumable_write`.

        Starts a resumable write. How long the write operation remains valid, and
        what happens when the write operation becomes invalid, are
        service-dependent.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].StartResumableWrite

    @property
    def query_write_status(self):
        """Return the gRPC stub for :meth:`StorageClient.query_write_status`.

        Determines the ``committed_size`` for an object that is being
        written, which can then be used as the ``write_offset`` for the next
        ``Write()`` call.

        If the object does not exist (i.e., the object has been deleted, or the
        first ``Write()`` has not yet reached the service), this method returns
        the error ``NOT_FOUND``.

        The client **may** call ``QueryWriteStatus()`` at any time to determine
        how much data has been processed for this object. This is useful if the
        client is buffering data and needs to know which data can be safely
        evicted. For any sequence of ``QueryWriteStatus()`` calls for a given
        object name, the sequence of returned ``committed_size`` values will be
        non-decreasing.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].QueryWriteStatus

    @property
    def patch_object(self):
        """Return the gRPC stub for :meth:`StorageClient.patch_object`.

        Updates an object's metadata.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].PatchObject

    @property
    def update_object(self):
        """Return the gRPC stub for :meth:`StorageClient.update_object`.

        Updates an object's metadata. Equivalent to PatchObject, but always
        replaces all mutatable fields of the bucket with new values, reverting all
        unspecified fields to their default values.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].UpdateObject

    @property
    def get_object_iam_policy(self):
        """Return the gRPC stub for :meth:`StorageClient.get_object_iam_policy`.

        Gets the IAM policy for the specified object.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetObjectIamPolicy

    @property
    def set_object_iam_policy(self):
        """Return the gRPC stub for :meth:`StorageClient.set_object_iam_policy`.

        Updates an IAM policy for the specified object.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].SetObjectIamPolicy

    @property
    def test_object_iam_permissions(self):
        """Return the gRPC stub for :meth:`StorageClient.test_object_iam_permissions`.

        Tests a set of permissions on the given object to see which, if
        any, are held by the caller.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].TestObjectIamPermissions

    @property
    def watch_all_objects(self):
        """Return the gRPC stub for :meth:`StorageClient.watch_all_objects`.

        Watch for changes on all objects in a bucket.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].WatchAllObjects

    @property
    def get_service_account(self):
        """Return the gRPC stub for :meth:`StorageClient.get_service_account`.

        Retrieves the name of a project's Google Cloud Storage service account.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetServiceAccount

    @property
    def create_hmac_key(self):
        """Return the gRPC stub for :meth:`StorageClient.create_hmac_key`.

        Creates a new HMAC key for the given service account.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].CreateHmacKey

    @property
    def delete_hmac_key(self):
        """Return the gRPC stub for :meth:`StorageClient.delete_hmac_key`.

        Deletes a given HMAC key.  Key must be in an INACTIVE state.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].DeleteHmacKey

    @property
    def get_hmac_key(self):
        """Return the gRPC stub for :meth:`StorageClient.get_hmac_key`.

        Gets an existing HMAC key metadata for the given id.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].GetHmacKey

    @property
    def list_hmac_keys(self):
        """Return the gRPC stub for :meth:`StorageClient.list_hmac_keys`.

        Lists HMAC keys under a given project with the additional filters provided.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].ListHmacKeys

    @property
    def update_hmac_key(self):
        """Return the gRPC stub for :meth:`StorageClient.update_hmac_key`.

        Updates a given HMAC key state between ACTIVE and INACTIVE.

        Returns:
            Callable: A callable which accepts the appropriate
                deserialized request object and returns a
                deserialized response object.
        """
        return self._stubs["storage_stub"].UpdateHmacKey
