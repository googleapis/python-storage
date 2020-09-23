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

"""Accesses the google.storage.v1 Storage API."""

import pkg_resources
import warnings

from google.oauth2 import service_account
import google.api_core.client_options
import google.api_core.gapic_v1.client_info
import google.api_core.gapic_v1.config
import google.api_core.gapic_v1.method
import google.api_core.grpc_helpers
import google.api_core.protobuf_helpers

from google.cloud.storage_v1 import storage_client_config
from google.cloud.storage_v1.proto import storage_pb2
from google.cloud.storage_v1.transports import storage_grpc_transport


_GAPIC_LIBRARY_VERSION = pkg_resources.get_distribution("google-cloud-storage",).version


class StorageClient(object):
    """Manages Google Cloud Storage resources."""

    SERVICE_ADDRESS = "storage.googleapis.com:443"
    """The default address of the service."""

    # The name of the interface for this client. This is the key used to
    # find the method configuration in the client_config dictionary.
    _INTERFACE_NAME = "google.storage.v1.Storage"

    @classmethod
    def from_service_account_file(cls, filename, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
        file.

        Args:
            filename (str): The path to the service account private key json
                file.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            StorageClient: The constructed client.
        """
        credentials = service_account.Credentials.from_service_account_file(filename)
        kwargs["credentials"] = credentials
        return cls(*args, **kwargs)

    from_service_account_json = from_service_account_file

    def __init__(
        self,
        transport=None,
        channel=None,
        credentials=None,
        client_config=None,
        client_info=None,
        client_options=None,
    ):
        """Constructor.

        Args:
            transport (Union[~.StorageGrpcTransport,
                    Callable[[~.Credentials, type], ~.StorageGrpcTransport]): A transport
                instance, responsible for actually making the API calls.
                The default transport uses the gRPC protocol.
                This argument may also be a callable which returns a
                transport instance. Callables will be sent the credentials
                as the first argument and the default transport class as
                the second argument.
            channel (grpc.Channel): DEPRECATED. A ``Channel`` instance
                through which to make calls. This argument is mutually exclusive
                with ``credentials``; providing both will raise an exception.
            credentials (google.auth.credentials.Credentials): The
                authorization credentials to attach to requests. These
                credentials identify this application to the service. If none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
                This argument is mutually exclusive with providing a
                transport instance to ``transport``; doing so will raise
                an exception.
            client_config (dict): DEPRECATED. A dictionary of call options for
                each method. If not specified, the default configuration is used.
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you're developing
                your own client library.
            client_options (Union[dict, google.api_core.client_options.ClientOptions]):
                Client options used to set user options on the client. API Endpoint
                should be set through client_options.
        """
        # Raise deprecation warnings for things we want to go away.
        if client_config is not None:
            warnings.warn(
                "The `client_config` argument is deprecated.",
                PendingDeprecationWarning,
                stacklevel=2,
            )
        else:
            client_config = storage_client_config.config

        if channel:
            warnings.warn(
                "The `channel` argument is deprecated; use " "`transport` instead.",
                PendingDeprecationWarning,
                stacklevel=2,
            )

        api_endpoint = self.SERVICE_ADDRESS
        if client_options:
            if type(client_options) == dict:
                client_options = google.api_core.client_options.from_dict(
                    client_options
                )
            if client_options.api_endpoint:
                api_endpoint = client_options.api_endpoint

        # Instantiate the transport.
        # The transport is responsible for handling serialization and
        # deserialization and actually sending data to the service.
        if transport:
            if callable(transport):
                self.transport = transport(
                    credentials=credentials,
                    default_class=storage_grpc_transport.StorageGrpcTransport,
                    address=api_endpoint,
                )
            else:
                if credentials:
                    raise ValueError(
                        "Received both a transport instance and "
                        "credentials; these are mutually exclusive."
                    )
                self.transport = transport
        else:
            self.transport = storage_grpc_transport.StorageGrpcTransport(
                address=api_endpoint, channel=channel, credentials=credentials,
            )

        if client_info is None:
            client_info = google.api_core.gapic_v1.client_info.ClientInfo(
                gapic_version=_GAPIC_LIBRARY_VERSION,
            )
        else:
            client_info.gapic_version = _GAPIC_LIBRARY_VERSION
        self._client_info = client_info

        # Parse out the default settings for retry and timeout for each RPC
        # from the client configuration.
        # (Ordinarily, these are the defaults specified in the `*_config.py`
        # file next to this one.)
        self._method_configs = google.api_core.gapic_v1.config.parse_method_configs(
            client_config["interfaces"][self._INTERFACE_NAME],
        )

        # Save a dictionary of cached API call functions.
        # These are the actual callables which invoke the proper
        # transport methods, wrapped with `wrap_method` to add retry,
        # timeout, and the like.
        self._inner_api_calls = {}

    # Service calls
    def delete_bucket_access_control(
        self,
        bucket,
        entity,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Permanently deletes the ACL entry for the specified entity on the specified
        bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> client.delete_bucket_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "delete_bucket_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "delete_bucket_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.delete_bucket_access_control,
                default_retry=self._method_configs["DeleteBucketAccessControl"].retry,
                default_timeout=self._method_configs[
                    "DeleteBucketAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.DeleteBucketAccessControlRequest(
            bucket=bucket, entity=entity, common_request_params=common_request_params,
        )
        self._inner_api_calls["delete_bucket_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_bucket_access_control(
        self,
        bucket,
        entity,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Returns the ACL entry for the specified entity on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> response = client.get_bucket_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.BucketAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_bucket_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_bucket_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_bucket_access_control,
                default_retry=self._method_configs["GetBucketAccessControl"].retry,
                default_timeout=self._method_configs["GetBucketAccessControl"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetBucketAccessControlRequest(
            bucket=bucket, entity=entity, common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_bucket_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def insert_bucket_access_control(
        self,
        bucket,
        bucket_access_control=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Creates a new ACL entry on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.insert_bucket_access_control(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            bucket_access_control (Union[dict, ~google.cloud.storage_v1.types.BucketAccessControl]): Properties of the new bucket access control being inserted.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.BucketAccessControl`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.BucketAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "insert_bucket_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "insert_bucket_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.insert_bucket_access_control,
                default_retry=self._method_configs["InsertBucketAccessControl"].retry,
                default_timeout=self._method_configs[
                    "InsertBucketAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.InsertBucketAccessControlRequest(
            bucket=bucket,
            bucket_access_control=bucket_access_control,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["insert_bucket_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_bucket_access_controls(
        self,
        bucket,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves ACL entries on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.list_bucket_access_controls(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListBucketAccessControlsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_bucket_access_controls" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_bucket_access_controls"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_bucket_access_controls,
                default_retry=self._method_configs["ListBucketAccessControls"].retry,
                default_timeout=self._method_configs[
                    "ListBucketAccessControls"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListBucketAccessControlsRequest(
            bucket=bucket, common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_bucket_access_controls"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def update_bucket_access_control(
        self,
        bucket,
        entity,
        bucket_access_control=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates an ACL entry on the specified bucket. Equivalent to
        PatchBucketAccessControl, but all unspecified fields will be
        reset to their default values.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> response = client.update_bucket_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            bucket_access_control (Union[dict, ~google.cloud.storage_v1.types.BucketAccessControl]): The BucketAccessControl for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.BucketAccessControl`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.BucketAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "update_bucket_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "update_bucket_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.update_bucket_access_control,
                default_retry=self._method_configs["UpdateBucketAccessControl"].retry,
                default_timeout=self._method_configs[
                    "UpdateBucketAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.UpdateBucketAccessControlRequest(
            bucket=bucket,
            entity=entity,
            bucket_access_control=bucket_access_control,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["update_bucket_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def patch_bucket_access_control(
        self,
        bucket,
        entity,
        bucket_access_control=None,
        update_mask=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates an ACL entry on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> response = client.patch_bucket_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            bucket_access_control (Union[dict, ~google.cloud.storage_v1.types.BucketAccessControl]): The BucketAccessControl for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.BucketAccessControl`
            update_mask (Union[dict, ~google.cloud.storage_v1.types.FieldMask]): List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's "update" function,
                specify a single field with the value ``*``.

                Not specifying any fields is an error. Not specifying a field while
                setting that field to a non-default value is an error.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.FieldMask`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.BucketAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "patch_bucket_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "patch_bucket_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.patch_bucket_access_control,
                default_retry=self._method_configs["PatchBucketAccessControl"].retry,
                default_timeout=self._method_configs[
                    "PatchBucketAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.PatchBucketAccessControlRequest(
            bucket=bucket,
            entity=entity,
            bucket_access_control=bucket_access_control,
            update_mask=update_mask,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["patch_bucket_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def delete_bucket(
        self,
        bucket,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Permanently deletes an empty bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> client.delete_bucket(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): If set, only deletes the bucket if its metageneration matches this value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): If set, only deletes the bucket if its metageneration does not match this
                value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "delete_bucket" not in self._inner_api_calls:
            self._inner_api_calls[
                "delete_bucket"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.delete_bucket,
                default_retry=self._method_configs["DeleteBucket"].retry,
                default_timeout=self._method_configs["DeleteBucket"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.DeleteBucketRequest(
            bucket=bucket,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            common_request_params=common_request_params,
        )
        self._inner_api_calls["delete_bucket"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_bucket(
        self,
        bucket,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        projection=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Returns metadata for the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.get_bucket(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the return of the bucket metadata conditional on whether the bucket's
                current metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the return of the bucket metadata conditional on whether the bucket's
                current metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Bucket` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_bucket" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_bucket"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_bucket,
                default_retry=self._method_configs["GetBucket"].retry,
                default_timeout=self._method_configs["GetBucket"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetBucketRequest(
            bucket=bucket,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            projection=projection,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_bucket"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def insert_bucket(
        self,
        project,
        predefined_acl=None,
        predefined_default_object_acl=None,
        projection=None,
        bucket=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Creates a new bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `project`:
            >>> project = ''
            >>>
            >>> response = client.insert_bucket(project)

        Args:
            project (str): Required. A valid API project identifier.
            predefined_acl (~google.cloud.storage_v1.types.PredefinedBucketAcl): Apply a predefined set of access controls to this bucket.
            predefined_default_object_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of default object access controls to this bucket.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``, unless the
                bucket resource specifies ``acl`` or ``defaultObjectAcl`` properties,
                when it defaults to ``FULL``.
            bucket (Union[dict, ~google.cloud.storage_v1.types.Bucket]): Properties of the new bucket being inserted, including its name.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Bucket`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Bucket` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "insert_bucket" not in self._inner_api_calls:
            self._inner_api_calls[
                "insert_bucket"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.insert_bucket,
                default_retry=self._method_configs["InsertBucket"].retry,
                default_timeout=self._method_configs["InsertBucket"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.InsertBucketRequest(
            project=project,
            predefined_acl=predefined_acl,
            predefined_default_object_acl=predefined_default_object_acl,
            projection=projection,
            bucket=bucket,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["insert_bucket"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_channels(
        self,
        bucket,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        List active object change notification channels for this bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.list_channels(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListChannelsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_channels" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_channels"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_channels,
                default_retry=self._method_configs["ListChannels"].retry,
                default_timeout=self._method_configs["ListChannels"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListChannelsRequest(
            bucket=bucket, common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_channels"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_buckets(
        self,
        project,
        max_results=None,
        page_token=None,
        prefix=None,
        projection=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves a list of buckets for a given project.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `project`:
            >>> project = ''
            >>>
            >>> response = client.list_buckets(project)

        Args:
            project (str): Required. A valid API project identifier.
            max_results (int): Maximum number of buckets to return in a single response. The service will
                use this parameter or 1,000 items, whichever is smaller.
            page_token (str): A previously-returned page token representing part of the larger set of
                results to view.
            prefix (str): Filter results to buckets whose names begin with this prefix.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListBucketsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_buckets" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_buckets"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_buckets,
                default_retry=self._method_configs["ListBuckets"].retry,
                default_timeout=self._method_configs["ListBuckets"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListBucketsRequest(
            project=project,
            max_results=max_results,
            page_token=page_token,
            prefix=prefix,
            projection=projection,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_buckets"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def lock_bucket_retention_policy(
        self,
        bucket,
        if_metageneration_match=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Locks retention policy on a bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.lock_bucket_retention_policy(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            if_metageneration_match (long): Makes the operation conditional on whether bucket's current metageneration
                matches the given value. Must be positive.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Bucket` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "lock_bucket_retention_policy" not in self._inner_api_calls:
            self._inner_api_calls[
                "lock_bucket_retention_policy"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.lock_bucket_retention_policy,
                default_retry=self._method_configs["LockBucketRetentionPolicy"].retry,
                default_timeout=self._method_configs[
                    "LockBucketRetentionPolicy"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.LockRetentionPolicyRequest(
            bucket=bucket,
            if_metageneration_match=if_metageneration_match,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["lock_bucket_retention_policy"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_bucket_iam_policy(
        self,
        iam_request=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Gets the IAM policy for the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.get_bucket_iam_policy()

        Args:
            iam_request (Union[dict, ~google.cloud.storage_v1.types.GetIamPolicyRequest]): The request sent to IAM.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.GetIamPolicyRequest`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Policy` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_bucket_iam_policy" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_bucket_iam_policy"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_bucket_iam_policy,
                default_retry=self._method_configs["GetBucketIamPolicy"].retry,
                default_timeout=self._method_configs["GetBucketIamPolicy"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetIamPolicyRequest(
            iam_request=iam_request, common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_bucket_iam_policy"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def set_bucket_iam_policy(
        self,
        iam_request=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates an IAM policy for the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.set_bucket_iam_policy()

        Args:
            iam_request (Union[dict, ~google.cloud.storage_v1.types.SetIamPolicyRequest]): The request sent to IAM.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.SetIamPolicyRequest`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Policy` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "set_bucket_iam_policy" not in self._inner_api_calls:
            self._inner_api_calls[
                "set_bucket_iam_policy"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.set_bucket_iam_policy,
                default_retry=self._method_configs["SetBucketIamPolicy"].retry,
                default_timeout=self._method_configs["SetBucketIamPolicy"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.SetIamPolicyRequest(
            iam_request=iam_request, common_request_params=common_request_params,
        )
        return self._inner_api_calls["set_bucket_iam_policy"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def test_bucket_iam_permissions(
        self,
        iam_request=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Tests a set of permissions on the given bucket to see which, if
        any, are held by the caller.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.test_bucket_iam_permissions()

        Args:
            iam_request (Union[dict, ~google.cloud.storage_v1.types.TestIamPermissionsRequest]): The request sent to IAM.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.TestIamPermissionsRequest`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.TestIamPermissionsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "test_bucket_iam_permissions" not in self._inner_api_calls:
            self._inner_api_calls[
                "test_bucket_iam_permissions"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.test_bucket_iam_permissions,
                default_retry=self._method_configs["TestBucketIamPermissions"].retry,
                default_timeout=self._method_configs[
                    "TestBucketIamPermissions"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.TestIamPermissionsRequest(
            iam_request=iam_request, common_request_params=common_request_params,
        )
        return self._inner_api_calls["test_bucket_iam_permissions"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def patch_bucket(
        self,
        bucket,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        predefined_acl=None,
        predefined_default_object_acl=None,
        projection=None,
        api_metadata=None,
        update_mask=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates a bucket. Changes to the bucket will be readable immediately after
        writing, but configuration changes may take time to propagate.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.patch_bucket(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the return of the bucket metadata conditional on whether the bucket's
                current metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the return of the bucket metadata conditional on whether the bucket's
                current metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            predefined_acl (~google.cloud.storage_v1.types.PredefinedBucketAcl): Apply a predefined set of access controls to this bucket.
            predefined_default_object_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of default object access controls to this bucket.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``FULL``.
            metadata (Union[dict, ~google.cloud.storage_v1.types.Bucket]): The Bucket metadata for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Bucket`
            update_mask (Union[dict, ~google.cloud.storage_v1.types.FieldMask]): List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's "update" function,
                specify a single field with the value ``*``. Note: not recommended. If a
                new field is introduced at a later time, an older client updating with
                the ``*`` may accidentally reset the new field's value.

                Not specifying any fields is an error. Not specifying a field while
                setting that field to a non-default value is an error.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.FieldMask`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Bucket` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "patch_bucket" not in self._inner_api_calls:
            self._inner_api_calls[
                "patch_bucket"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.patch_bucket,
                default_retry=self._method_configs["PatchBucket"].retry,
                default_timeout=self._method_configs["PatchBucket"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.PatchBucketRequest(
            bucket=bucket,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            predefined_acl=predefined_acl,
            predefined_default_object_acl=predefined_default_object_acl,
            projection=projection,
            metadata=api_metadata,
            update_mask=update_mask,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["patch_bucket"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def update_bucket(
        self,
        bucket,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        predefined_acl=None,
        predefined_default_object_acl=None,
        projection=None,
        api_metadata=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates a bucket. Equivalent to PatchBucket, but always replaces all
        mutatable fields of the bucket with new values, reverting all
        unspecified fields to their default values.
        Like PatchBucket, Changes to the bucket will be readable immediately after
        writing, but configuration changes may take time to propagate.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.update_bucket(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the return of the bucket metadata conditional on whether the bucket's
                current metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the return of the bucket metadata conditional on whether the bucket's
                current metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            predefined_acl (~google.cloud.storage_v1.types.PredefinedBucketAcl): Apply a predefined set of access controls to this bucket.
            predefined_default_object_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of default object access controls to this bucket.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``FULL``.
            metadata (Union[dict, ~google.cloud.storage_v1.types.Bucket]): The Bucket metadata for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Bucket`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Bucket` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "update_bucket" not in self._inner_api_calls:
            self._inner_api_calls[
                "update_bucket"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.update_bucket,
                default_retry=self._method_configs["UpdateBucket"].retry,
                default_timeout=self._method_configs["UpdateBucket"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.UpdateBucketRequest(
            bucket=bucket,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            predefined_acl=predefined_acl,
            predefined_default_object_acl=predefined_default_object_acl,
            projection=projection,
            metadata=api_metadata,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["update_bucket"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def stop_channel(
        self,
        channel=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Halts "Object Change Notification" push messagages.
        See https://cloud.google.com/storage/docs/object-change-notification
        Note: this is not related to the newer "Notifications" resource, which
        are stopped using DeleteNotification.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> client.stop_channel()

        Args:
            channel (Union[dict, ~google.cloud.storage_v1.types.Channel]): The channel to be stopped.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Channel`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "stop_channel" not in self._inner_api_calls:
            self._inner_api_calls[
                "stop_channel"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.stop_channel,
                default_retry=self._method_configs["StopChannel"].retry,
                default_timeout=self._method_configs["StopChannel"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.StopChannelRequest(
            channel=channel, common_request_params=common_request_params,
        )
        self._inner_api_calls["stop_channel"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def delete_default_object_access_control(
        self,
        bucket,
        entity,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Permanently deletes the default object ACL entry for the specified entity
        on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> client.delete_default_object_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "delete_default_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "delete_default_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.delete_default_object_access_control,
                default_retry=self._method_configs[
                    "DeleteDefaultObjectAccessControl"
                ].retry,
                default_timeout=self._method_configs[
                    "DeleteDefaultObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.DeleteDefaultObjectAccessControlRequest(
            bucket=bucket, entity=entity, common_request_params=common_request_params,
        )
        self._inner_api_calls["delete_default_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_default_object_access_control(
        self,
        bucket,
        entity,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Returns the default object ACL entry for the specified entity on the
        specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> response = client.get_default_object_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_default_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_default_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_default_object_access_control,
                default_retry=self._method_configs[
                    "GetDefaultObjectAccessControl"
                ].retry,
                default_timeout=self._method_configs[
                    "GetDefaultObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetDefaultObjectAccessControlRequest(
            bucket=bucket, entity=entity, common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_default_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def insert_default_object_access_control(
        self,
        bucket,
        object_access_control=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Creates a new default object ACL entry on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.insert_default_object_access_control(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            object_access_control (Union[dict, ~google.cloud.storage_v1.types.ObjectAccessControl]): Properties of the object access control being inserted.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.ObjectAccessControl`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "insert_default_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "insert_default_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.insert_default_object_access_control,
                default_retry=self._method_configs[
                    "InsertDefaultObjectAccessControl"
                ].retry,
                default_timeout=self._method_configs[
                    "InsertDefaultObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.InsertDefaultObjectAccessControlRequest(
            bucket=bucket,
            object_access_control=object_access_control,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["insert_default_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_default_object_access_controls(
        self,
        bucket,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves default object ACL entries on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.list_default_object_access_controls(bucket)

        Args:
            bucket (str): Required. Name of a bucket.
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): If present, only return default ACL listing if the bucket's current
                metageneration matches this value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): If present, only return default ACL listing if the bucket's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListObjectAccessControlsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_default_object_access_controls" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_default_object_access_controls"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_default_object_access_controls,
                default_retry=self._method_configs[
                    "ListDefaultObjectAccessControls"
                ].retry,
                default_timeout=self._method_configs[
                    "ListDefaultObjectAccessControls"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListDefaultObjectAccessControlsRequest(
            bucket=bucket,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_default_object_access_controls"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def patch_default_object_access_control(
        self,
        bucket,
        entity,
        object_access_control=None,
        update_mask=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates a default object ACL entry on the specified bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> response = client.patch_default_object_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            object_access_control (Union[dict, ~google.cloud.storage_v1.types.ObjectAccessControl]): The ObjectAccessControl for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.ObjectAccessControl`
            update_mask (Union[dict, ~google.cloud.storage_v1.types.FieldMask]): List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's "update" function,
                specify a single field with the value ``*``. Note: not recommended. If a
                new field is introduced at a later time, an older client updating with
                the ``*`` may accidentally reset the new field's value.

                Not specifying any fields is an error. Not specifying a field while
                setting that field to a non-default value is an error.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.FieldMask`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "patch_default_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "patch_default_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.patch_default_object_access_control,
                default_retry=self._method_configs[
                    "PatchDefaultObjectAccessControl"
                ].retry,
                default_timeout=self._method_configs[
                    "PatchDefaultObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.PatchDefaultObjectAccessControlRequest(
            bucket=bucket,
            entity=entity,
            object_access_control=object_access_control,
            update_mask=update_mask,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["patch_default_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def update_default_object_access_control(
        self,
        bucket,
        entity,
        object_access_control=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates a default object ACL entry on the specified bucket. Equivalent to
        PatchDefaultObjectAccessControl, but modifies all unspecified fields to
        their default values.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> response = client.update_default_object_access_control(bucket, entity)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            object_access_control (Union[dict, ~google.cloud.storage_v1.types.ObjectAccessControl]): The ObjectAccessControl for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.ObjectAccessControl`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "update_default_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "update_default_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.update_default_object_access_control,
                default_retry=self._method_configs[
                    "UpdateDefaultObjectAccessControl"
                ].retry,
                default_timeout=self._method_configs[
                    "UpdateDefaultObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.UpdateDefaultObjectAccessControlRequest(
            bucket=bucket,
            entity=entity,
            object_access_control=object_access_control,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["update_default_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def delete_notification(
        self,
        bucket,
        notification,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Permanently deletes a notification subscription.
        Note: Older, "Object Change Notification" push subscriptions should be
        deleted using StopChannel instead.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `notification`:
            >>> notification = ''
            >>>
            >>> client.delete_notification(bucket, notification)

        Args:
            bucket (str): Required. The parent bucket of the notification.
            notification (str): Required. ID of the notification to delete.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "delete_notification" not in self._inner_api_calls:
            self._inner_api_calls[
                "delete_notification"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.delete_notification,
                default_retry=self._method_configs["DeleteNotification"].retry,
                default_timeout=self._method_configs["DeleteNotification"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.DeleteNotificationRequest(
            bucket=bucket,
            notification=notification,
            common_request_params=common_request_params,
        )
        self._inner_api_calls["delete_notification"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_notification(
        self,
        bucket,
        notification,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        View a notification configuration.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `notification`:
            >>> notification = ''
            >>>
            >>> response = client.get_notification(bucket, notification)

        Args:
            bucket (str): Required. The parent bucket of the notification.
            notification (str): Required. Notification ID.
                Required.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Notification` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_notification" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_notification"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_notification,
                default_retry=self._method_configs["GetNotification"].retry,
                default_timeout=self._method_configs["GetNotification"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetNotificationRequest(
            bucket=bucket,
            notification=notification,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_notification"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def insert_notification(
        self,
        bucket,
        notification=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Creates a notification subscription for a given bucket.
        These notifications, when triggered, publish messages to the specified
        Cloud Pub/Sub topics.
        See https://cloud.google.com/storage/docs/pubsub-notifications.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.insert_notification(bucket)

        Args:
            bucket (str): Required. The parent bucket of the notification.
            notification (Union[dict, ~google.cloud.storage_v1.types.Notification]): Properties of the notification to be inserted.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Notification`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Notification` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "insert_notification" not in self._inner_api_calls:
            self._inner_api_calls[
                "insert_notification"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.insert_notification,
                default_retry=self._method_configs["InsertNotification"].retry,
                default_timeout=self._method_configs["InsertNotification"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.InsertNotificationRequest(
            bucket=bucket,
            notification=notification,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["insert_notification"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_notifications(
        self,
        bucket,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves a list of notification subscriptions for a given bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.list_notifications(bucket)

        Args:
            bucket (str): Required. Name of a Google Cloud Storage bucket.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListNotificationsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_notifications" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_notifications"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_notifications,
                default_retry=self._method_configs["ListNotifications"].retry,
                default_timeout=self._method_configs["ListNotifications"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListNotificationsRequest(
            bucket=bucket, common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_notifications"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def delete_object_access_control(
        self,
        bucket,
        entity,
        object_,
        generation=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Permanently deletes the ACL entry for the specified entity on the specified
        object.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> client.delete_object_access_control(bucket, entity, object_)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            object_ (str): Required. Name of the object.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "delete_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "delete_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.delete_object_access_control,
                default_retry=self._method_configs["DeleteObjectAccessControl"].retry,
                default_timeout=self._method_configs[
                    "DeleteObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.DeleteObjectAccessControlRequest(
            bucket=bucket,
            entity=entity,
            object=object_,
            generation=generation,
            common_request_params=common_request_params,
        )
        self._inner_api_calls["delete_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_object_access_control(
        self,
        bucket,
        entity,
        object_,
        generation=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Returns the ACL entry for the specified entity on the specified object.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.get_object_access_control(bucket, entity, object_)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            object_ (str): Required. Name of the object.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_object_access_control,
                default_retry=self._method_configs["GetObjectAccessControl"].retry,
                default_timeout=self._method_configs["GetObjectAccessControl"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetObjectAccessControlRequest(
            bucket=bucket,
            entity=entity,
            object=object_,
            generation=generation,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def insert_object_access_control(
        self,
        bucket,
        object_,
        generation=None,
        object_access_control=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Creates a new ACL entry on the specified object.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.insert_object_access_control(bucket, object_)

        Args:
            bucket (str): Required. Name of a bucket.
            object_ (str): Required. Name of the object.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            object_access_control (Union[dict, ~google.cloud.storage_v1.types.ObjectAccessControl]): Properties of the object access control to be inserted.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.ObjectAccessControl`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "insert_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "insert_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.insert_object_access_control,
                default_retry=self._method_configs["InsertObjectAccessControl"].retry,
                default_timeout=self._method_configs[
                    "InsertObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.InsertObjectAccessControlRequest(
            bucket=bucket,
            object=object_,
            generation=generation,
            object_access_control=object_access_control,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["insert_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_object_access_controls(
        self,
        bucket,
        object_,
        generation=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves ACL entries on the specified object.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.list_object_access_controls(bucket, object_)

        Args:
            bucket (str): Required. Name of a bucket.
            object_ (str): Required. Name of the object.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListObjectAccessControlsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_object_access_controls" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_object_access_controls"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_object_access_controls,
                default_retry=self._method_configs["ListObjectAccessControls"].retry,
                default_timeout=self._method_configs[
                    "ListObjectAccessControls"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListObjectAccessControlsRequest(
            bucket=bucket,
            object=object_,
            generation=generation,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_object_access_controls"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def patch_object_access_control(
        self,
        bucket,
        entity,
        object_,
        generation=None,
        object_access_control=None,
        common_request_params=None,
        update_mask=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Patches an ACL entry on the specified object. Patch is similar to
        update, but only applies or appends the specified fields in the
        object_access_control object. Other fields are unaffected.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.patch_object_access_control(bucket, entity, object_)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            object_ (str): Required. Name of the object.
                Required.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            object_access_control (Union[dict, ~google.cloud.storage_v1.types.ObjectAccessControl]): The ObjectAccessControl for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.ObjectAccessControl`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            update_mask (Union[dict, ~google.cloud.storage_v1.types.FieldMask]): List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's "update" function,
                specify a single field with the value ``*``. Note: not recommended. If a
                new field is introduced at a later time, an older client updating with
                the ``*`` may accidentally reset the new field's value.

                Not specifying any fields is an error. Not specifying a field while
                setting that field to a non-default value is an error.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.FieldMask`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "patch_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "patch_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.patch_object_access_control,
                default_retry=self._method_configs["PatchObjectAccessControl"].retry,
                default_timeout=self._method_configs[
                    "PatchObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.PatchObjectAccessControlRequest(
            bucket=bucket,
            entity=entity,
            object=object_,
            generation=generation,
            object_access_control=object_access_control,
            common_request_params=common_request_params,
            update_mask=update_mask,
        )
        return self._inner_api_calls["patch_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def update_object_access_control(
        self,
        bucket,
        entity,
        object_,
        generation=None,
        object_access_control=None,
        common_request_params=None,
        update_mask=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates an ACL entry on the specified object.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `entity`:
            >>> entity = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.update_object_access_control(bucket, entity, object_)

        Args:
            bucket (str): Required. Name of a bucket.
            entity (str): Required. The entity holding the permission. Can be one of:

                -  ``user-`` *userId*
                -  ``user-`` *emailAddress*
                -  ``group-`` *groupId*
                -  ``group-`` *emailAddress*
                -  ``allUsers``
                -  ``allAuthenticatedUsers``
            object_ (str): Required. Name of the object.
                Required.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            object_access_control (Union[dict, ~google.cloud.storage_v1.types.ObjectAccessControl]): The ObjectAccessControl for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.ObjectAccessControl`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            update_mask (Union[dict, ~google.cloud.storage_v1.types.FieldMask]): List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's "update" function,
                specify a single field with the value ``*``. Note: not recommended. If a
                new field is introduced at a later time, an older client updating with
                the ``*`` may accidentally reset the new field's value.

                Not specifying any fields is an error. Not specifying a field while
                setting that field to a non-default value is an error.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.FieldMask`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ObjectAccessControl` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "update_object_access_control" not in self._inner_api_calls:
            self._inner_api_calls[
                "update_object_access_control"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.update_object_access_control,
                default_retry=self._method_configs["UpdateObjectAccessControl"].retry,
                default_timeout=self._method_configs[
                    "UpdateObjectAccessControl"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.UpdateObjectAccessControlRequest(
            bucket=bucket,
            entity=entity,
            object=object_,
            generation=generation,
            object_access_control=object_access_control,
            common_request_params=common_request_params,
            update_mask=update_mask,
        )
        return self._inner_api_calls["update_object_access_control"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def compose_object(
        self,
        destination_bucket,
        destination_object,
        destination_predefined_acl=None,
        destination=None,
        source_objects=None,
        if_generation_match=None,
        if_metageneration_match=None,
        kms_key_name=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Concatenates a list of existing objects into a new object in the same
        bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `destination_bucket`:
            >>> destination_bucket = ''
            >>>
            >>> # TODO: Initialize `destination_object`:
            >>> destination_object = ''
            >>>
            >>> response = client.compose_object(destination_bucket, destination_object)

        Args:
            destination_bucket (str): Required. Name of the bucket containing the source objects. The destination object is
                stored in this bucket.
            destination_object (str): Required. Name of the new object.
            destination_predefined_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of access controls to the destination object.
            destination (Union[dict, ~google.cloud.storage_v1.types.Object]): Properties of the resulting object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Object`
            source_objects (list[Union[dict, ~google.cloud.storage_v1.types.SourceObjects]]): The list of source objects that will be concatenated into a single object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.SourceObjects`
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                matches the given value. Setting to 0 makes the operation succeed only if
                there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            kms_key_name (str): Resource name of the Cloud KMS key, of the form
                ``projects/my-project/locations/my-location/keyRings/my-kr/cryptoKeys/my-key``,
                that will be used to encrypt the object. Overrides the object metadata's
                ``kms_key_name`` value, if any.
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Object` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "compose_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "compose_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.compose_object,
                default_retry=self._method_configs["ComposeObject"].retry,
                default_timeout=self._method_configs["ComposeObject"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ComposeObjectRequest(
            destination_bucket=destination_bucket,
            destination_object=destination_object,
            destination_predefined_acl=destination_predefined_acl,
            destination=destination,
            source_objects=source_objects,
            if_generation_match=if_generation_match,
            if_metageneration_match=if_metageneration_match,
            kms_key_name=kms_key_name,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["compose_object"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def copy_object(
        self,
        destination_bucket,
        destination_object,
        source_bucket,
        source_object,
        destination_predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        if_source_generation_match=None,
        if_source_generation_not_match=None,
        if_source_metageneration_match=None,
        if_source_metageneration_not_match=None,
        projection=None,
        source_generation=None,
        destination=None,
        destination_kms_key_name=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Copies a source object to a destination object. Optionally overrides
        metadata.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `destination_bucket`:
            >>> destination_bucket = ''
            >>>
            >>> # TODO: Initialize `destination_object`:
            >>> destination_object = ''
            >>>
            >>> # TODO: Initialize `source_bucket`:
            >>> source_bucket = ''
            >>>
            >>> # TODO: Initialize `source_object`:
            >>> source_object = ''
            >>>
            >>> response = client.copy_object(destination_bucket, destination_object, source_bucket, source_object)

        Args:
            destination_bucket (str): Required. Name of the bucket in which to store the new object.
                Overrides the provided object metadata's ``bucket`` value, if any.
            destination_object (str): Required. Name of the new object. Required when the object metadata
                is not otherwise provided. Overrides the object metadata's ``name``
                value, if any.
            source_bucket (str): Required. Name of the bucket in which to find the source object.
            source_object (str): Required. Name of the source object.
            destination_predefined_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of access controls to the destination object.
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the destination object's current
                generation matches the given value. Setting to 0 makes the operation
                succeed only if there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the destination object's current
                generation does not match the given value. If no live object exists, the
                precondition fails. Setting to 0 makes the operation succeed only if there
                is a live version of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the destination object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the destination object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                generation matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                generation does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``, unless the
                object resource specifies the ``acl`` property, when it defaults to
                ``full``.
            source_generation (long): If present, selects a specific revision of the source object (as opposed to
                the latest version, the default).
            destination (Union[dict, ~google.cloud.storage_v1.types.Object]): Properties of the resulting object. If not set, duplicate properties of
                source object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Object`
            destination_kms_key_name (str): Resource name of the Cloud KMS key, of the form
                ``projects/my-project/locations/my-location/keyRings/my-kr/cryptoKeys/my-key``,
                that will be used to encrypt the object. Overrides the object metadata's
                ``kms_key_name`` value, if any.
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Object` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "copy_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "copy_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.copy_object,
                default_retry=self._method_configs["CopyObject"].retry,
                default_timeout=self._method_configs["CopyObject"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.CopyObjectRequest(
            destination_bucket=destination_bucket,
            destination_object=destination_object,
            source_bucket=source_bucket,
            source_object=source_object,
            destination_predefined_acl=destination_predefined_acl,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            if_source_generation_match=if_source_generation_match,
            if_source_generation_not_match=if_source_generation_not_match,
            if_source_metageneration_match=if_source_metageneration_match,
            if_source_metageneration_not_match=if_source_metageneration_not_match,
            projection=projection,
            source_generation=source_generation,
            destination=destination,
            destination_kms_key_name=destination_kms_key_name,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["copy_object"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def delete_object(
        self,
        bucket,
        object_,
        upload_id=None,
        generation=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Deletes an object and its metadata. Deletions are permanent if
        versioning is not enabled for the bucket, or if the ``generation``
        parameter is used.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> client.delete_object(bucket, object_)

        Args:
            bucket (str): Required. Name of the bucket in which the object resides.
            object_ (str): Required. The name of the object to delete (when not using a resumable write).
            upload_id (str): The resumable upload_id of the object to delete (when using a
                resumable write). This should be copied from the ``upload_id`` field of
                ``StartResumableWriteResponse``.
            generation (long): If present, permanently deletes a specific revision of this object (as
                opposed to the latest version, the default).
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                matches the given value. Setting to 0 makes the operation succeed only if
                there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                does not match the given value. If no live object exists, the precondition
                fails. Setting to 0 makes the operation succeed only if there is a live
                version of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "delete_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "delete_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.delete_object,
                default_retry=self._method_configs["DeleteObject"].retry,
                default_timeout=self._method_configs["DeleteObject"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.DeleteObjectRequest(
            bucket=bucket,
            object=object_,
            upload_id=upload_id,
            generation=generation,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        self._inner_api_calls["delete_object"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_object(
        self,
        bucket,
        object_,
        generation=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        projection=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves an object's metadata.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.get_object(bucket, object_)

        Args:
            bucket (str): Required. Name of the bucket in which the object resides.
            object_ (str): Required. Name of the object.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                matches the given value. Setting to 0 makes the operation succeed only if
                there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                does not match the given value. If no live object exists, the precondition
                fails. Setting to 0 makes the operation succeed only if there is a live
                version of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``.
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Object` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_object,
                default_retry=self._method_configs["GetObject"].retry,
                default_timeout=self._method_configs["GetObject"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetObjectRequest(
            bucket=bucket,
            object=object_,
            generation=generation,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            projection=projection,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_object"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_object_media(
        self,
        bucket=None,
        object_=None,
        generation=None,
        read_offset=None,
        read_limit=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Reads an object's data.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> for element in client.get_object_media():
            ...     # process element
            ...     pass

        Args:
            bucket (str): The name of the bucket containing the object to read.
            object_ (str): The name of the object to read.
            generation (long): If present, selects a specific revision of this object (as opposed
                to the latest version, the default).
            read_offset (long): The offset for the first byte to return in the read, relative to the
                start of the object.

                A negative ``read_offset`` value will be interpreted as the number of
                bytes back from the end of the object to be returned. For example, if an
                object's length is 15 bytes, a GetObjectMediaRequest with
                ``read_offset`` = -5 and ``read_limit`` = 3 would return bytes 10
                through 12 of the object.
            read_limit (long): The maximum number of ``data`` bytes the server is allowed to return
                in the sum of all ``Object`` messages. A ``read_limit`` of zero
                indicates that there is no limit, and a negative ``read_limit`` will
                cause an error.

                If the stream returns fewer bytes than allowed by the ``read_limit`` and
                no error occurred, the stream includes all data from the ``read_offset``
                to the end of the resource.
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                matches the given value. Setting to 0 makes the operation succeed only if
                there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                does not match the given value. If no live object exists, the precondition
                fails. Setting to 0 makes the operation succeed only if there is a live
                version of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            Iterable[~google.cloud.storage_v1.types.GetObjectMediaResponse].

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_object_media" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_object_media"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_object_media,
                default_retry=self._method_configs["GetObjectMedia"].retry,
                default_timeout=self._method_configs["GetObjectMedia"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetObjectMediaRequest(
            bucket=bucket,
            object=object_,
            generation=generation,
            read_offset=read_offset,
            read_limit=read_limit,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_object_media"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def insert_object(
        self,
        requests,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
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

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `write_offset`:
            >>> write_offset = 0
            >>> request = {'write_offset': write_offset}
            >>>
            >>> requests = [request]
            >>> response = client.insert_object(requests)

        Args:
            requests (iterator[dict|google.cloud.storage_v1.proto.storage_pb2.InsertObjectRequest]): The input objects. If a dict is provided, it must be of the
                same form as the protobuf message :class:`~google.cloud.storage_v1.types.InsertObjectRequest`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Object` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "insert_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "insert_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.insert_object,
                default_retry=self._method_configs["InsertObject"].retry,
                default_timeout=self._method_configs["InsertObject"].timeout,
                client_info=self._client_info,
            )

        return self._inner_api_calls["insert_object"](
            requests, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_objects(
        self,
        bucket,
        delimiter=None,
        include_trailing_delimiter=None,
        max_results=None,
        page_token=None,
        prefix=None,
        projection=None,
        versions=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves a list of objects matching the criteria.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> response = client.list_objects(bucket)

        Args:
            bucket (str): Required. Name of the bucket in which to look for objects.
            delimiter (str): Returns results in a directory-like mode. ``items`` will contain
                only objects whose names, aside from the ``prefix``, do not contain
                ``delimiter``. Objects whose names, aside from the ``prefix``, contain
                ``delimiter`` will have their name, truncated after the ``delimiter``,
                returned in ``prefixes``. Duplicate ``prefixes`` are omitted.
            include_trailing_delimiter (bool): If true, objects that end in exactly one instance of ``delimiter``
                will have their metadata included in ``items`` in addition to
                ``prefixes``.
            max_results (int): Maximum number of ``items`` plus ``prefixes`` to return in a single
                page of responses. As duplicate ``prefixes`` are omitted, fewer total
                results may be returned than requested. The service will use this
                parameter or 1,000 items, whichever is smaller.
            page_token (str): A previously-returned page token representing part of the larger set of
                results to view.
            prefix (str): Filter results to objects whose names begin with this prefix.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``.
            versions (bool): If ``true``, lists all versions of an object as distinct results.
                The default is ``false``. For more information, see `Object
                Versioning <https://cloud.google.com/storage/docs/object-versioning>`__.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListObjectsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_objects" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_objects"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_objects,
                default_retry=self._method_configs["ListObjects"].retry,
                default_timeout=self._method_configs["ListObjects"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListObjectsRequest(
            bucket=bucket,
            delimiter=delimiter,
            include_trailing_delimiter=include_trailing_delimiter,
            max_results=max_results,
            page_token=page_token,
            prefix=prefix,
            projection=projection,
            versions=versions,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_objects"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def rewrite_object(
        self,
        destination_bucket,
        destination_object,
        source_bucket,
        source_object,
        destination_kms_key_name=None,
        destination_predefined_acl=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        if_source_generation_match=None,
        if_source_generation_not_match=None,
        if_source_metageneration_match=None,
        if_source_metageneration_not_match=None,
        max_bytes_rewritten_per_call=None,
        projection=None,
        rewrite_token=None,
        source_generation=None,
        object_=None,
        copy_source_encryption_algorithm=None,
        copy_source_encryption_key=None,
        copy_source_encryption_key_sha256=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Rewrites a source object to a destination object. Optionally overrides
        metadata.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `destination_bucket`:
            >>> destination_bucket = ''
            >>>
            >>> # TODO: Initialize `destination_object`:
            >>> destination_object = ''
            >>>
            >>> # TODO: Initialize `source_bucket`:
            >>> source_bucket = ''
            >>>
            >>> # TODO: Initialize `source_object`:
            >>> source_object = ''
            >>>
            >>> response = client.rewrite_object(destination_bucket, destination_object, source_bucket, source_object)

        Args:
            destination_bucket (str): Required. Name of the bucket in which to store the new object.
                Overrides the provided object metadata's ``bucket`` value, if any.
            destination_object (str): Required. Name of the new object. Required when the object metadata
                is not otherwise provided. Overrides the object metadata's ``name``
                value, if any.
            source_bucket (str): Required. Name of the bucket in which to find the source object.
            source_object (str): Required. Name of the source object.
            destination_kms_key_name (str): Resource name of the Cloud KMS key, of the form
                ``projects/my-project/locations/my-location/keyRings/my-kr/cryptoKeys/my-key``,
                that will be used to encrypt the object. Overrides the object metadata's
                ``kms_key_name`` value, if any.
            destination_predefined_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of access controls to the destination object.
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                matches the given value. Setting to 0 makes the operation succeed only if
                there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                does not match the given value. If no live object exists, the precondition
                fails. Setting to 0 makes the operation succeed only if there is a live
                version of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the destination object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the destination object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                generation matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                generation does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_source_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the source object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            max_bytes_rewritten_per_call (long): The maximum number of bytes that will be rewritten per rewrite
                request. Most callers shouldn't need to specify this parameter - it is
                primarily in place to support testing. If specified the value must be an
                integral multiple of 1 MiB (1048576). Also, this only applies to
                requests where the source and destination span locations and/or storage
                classes. Finally, this value must not change across rewrite calls else
                you'll get an error that the ``rewriteToken`` is invalid.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``, unless the
                object resource specifies the ``acl`` property, when it defaults to
                ``full``.
            rewrite_token (str): Include this field (from the previous rewrite response) on each rewrite
                request after the first one, until the rewrite response 'done' flag is
                true. Calls that provide a rewriteToken can omit all other request fields,
                but if included those fields must match the values provided in the first
                rewrite request.
            source_generation (long): If present, selects a specific revision of the source object (as opposed to
                the latest version, the default).
            object_ (Union[dict, ~google.cloud.storage_v1.types.Object]): Properties of the destination, post-rewrite object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Object`
            copy_source_encryption_algorithm (str): The algorithm used to encrypt the source object, if any.
            copy_source_encryption_key (str): The encryption key used to encrypt the source object, if any.
            copy_source_encryption_key_sha256 (str): The SHA-256 hash of the key used to encrypt the source object, if any.
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.RewriteResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "rewrite_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "rewrite_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.rewrite_object,
                default_retry=self._method_configs["RewriteObject"].retry,
                default_timeout=self._method_configs["RewriteObject"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.RewriteObjectRequest(
            destination_bucket=destination_bucket,
            destination_object=destination_object,
            source_bucket=source_bucket,
            source_object=source_object,
            destination_kms_key_name=destination_kms_key_name,
            destination_predefined_acl=destination_predefined_acl,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            if_source_generation_match=if_source_generation_match,
            if_source_generation_not_match=if_source_generation_not_match,
            if_source_metageneration_match=if_source_metageneration_match,
            if_source_metageneration_not_match=if_source_metageneration_not_match,
            max_bytes_rewritten_per_call=max_bytes_rewritten_per_call,
            projection=projection,
            rewrite_token=rewrite_token,
            source_generation=source_generation,
            object=object_,
            copy_source_encryption_algorithm=copy_source_encryption_algorithm,
            copy_source_encryption_key=copy_source_encryption_key,
            copy_source_encryption_key_sha256=copy_source_encryption_key_sha256,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["rewrite_object"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def start_resumable_write(
        self,
        insert_object_spec=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Starts a resumable write. How long the write operation remains valid, and
        what happens when the write operation becomes invalid, are
        service-dependent.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.start_resumable_write()

        Args:
            insert_object_spec (Union[dict, ~google.cloud.storage_v1.types.InsertObjectSpec]): The destination bucket, object, and metadata, as well as any preconditions.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.InsertObjectSpec`
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.StartResumableWriteResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "start_resumable_write" not in self._inner_api_calls:
            self._inner_api_calls[
                "start_resumable_write"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.start_resumable_write,
                default_retry=self._method_configs["StartResumableWrite"].retry,
                default_timeout=self._method_configs["StartResumableWrite"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.StartResumableWriteRequest(
            insert_object_spec=insert_object_spec,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["start_resumable_write"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def query_write_status(
        self,
        upload_id,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
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

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `upload_id`:
            >>> upload_id = ''
            >>>
            >>> response = client.query_write_status(upload_id)

        Args:
            upload_id (str): Required. The name of the resume token for the object whose write status is being
                requested.
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.QueryWriteStatusResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "query_write_status" not in self._inner_api_calls:
            self._inner_api_calls[
                "query_write_status"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.query_write_status,
                default_retry=self._method_configs["QueryWriteStatus"].retry,
                default_timeout=self._method_configs["QueryWriteStatus"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.QueryWriteStatusRequest(
            upload_id=upload_id,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["query_write_status"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def patch_object(
        self,
        bucket,
        object_,
        generation=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        predefined_acl=None,
        projection=None,
        api_metadata=None,
        update_mask=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates an object's metadata.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.patch_object(bucket, object_)

        Args:
            bucket (str): Required. Name of the bucket in which the object resides.
            object_ (str): Required. Name of the object.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                matches the given value. Setting to 0 makes the operation succeed only if
                there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                does not match the given value. If no live object exists, the precondition
                fails. Setting to 0 makes the operation succeed only if there is a live
                version of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            predefined_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of access controls to this object.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``FULL``.
            metadata (Union[dict, ~google.cloud.storage_v1.types.Object]): The Object metadata for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Object`
            update_mask (Union[dict, ~google.cloud.storage_v1.types.FieldMask]): List of fields to be updated.

                To specify ALL fields, equivalent to the JSON API's "update" function,
                specify a single field with the value ``*``. Note: not recommended. If a
                new field is introduced at a later time, an older client updating with
                the ``*`` may accidentally reset the new field's value.

                Not specifying any fields is an error. Not specifying a field while
                setting that field to a non-default value is an error.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.FieldMask`
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Object` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "patch_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "patch_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.patch_object,
                default_retry=self._method_configs["PatchObject"].retry,
                default_timeout=self._method_configs["PatchObject"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.PatchObjectRequest(
            bucket=bucket,
            object=object_,
            generation=generation,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            predefined_acl=predefined_acl,
            projection=projection,
            metadata=api_metadata,
            update_mask=update_mask,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["patch_object"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def update_object(
        self,
        bucket,
        object_,
        generation=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        predefined_acl=None,
        projection=None,
        api_metadata=None,
        common_object_request_params=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates an object's metadata. Equivalent to PatchObject, but always
        replaces all mutatable fields of the bucket with new values, reverting all
        unspecified fields to their default values.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `bucket`:
            >>> bucket = ''
            >>>
            >>> # TODO: Initialize `object_`:
            >>> object_ = ''
            >>>
            >>> response = client.update_object(bucket, object_)

        Args:
            bucket (str): Required. Name of the bucket in which the object resides.
            object_ (str): Required. Name of the object.
            generation (long): If present, selects a specific revision of this object (as opposed to the
                latest version, the default).
            if_generation_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                matches the given value. Setting to 0 makes the operation succeed only if
                there are no live versions of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_generation_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current generation
                does not match the given value. If no live object exists, the precondition
                fails. Setting to 0 makes the operation succeed only if there is a live
                version of the object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration matches the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            if_metageneration_not_match (Union[dict, ~google.cloud.storage_v1.types.Int64Value]): Makes the operation conditional on whether the object's current
                metageneration does not match the given value.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Int64Value`
            predefined_acl (~google.cloud.storage_v1.types.PredefinedObjectAcl): Apply a predefined set of access controls to this object.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``FULL``.
            metadata (Union[dict, ~google.cloud.storage_v1.types.Object]): The Object metadata for updating.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Object`
            common_object_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonObjectRequestParams]): A set of parameters common to Storage API requests concerning an object.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonObjectRequestParams`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Object` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "update_object" not in self._inner_api_calls:
            self._inner_api_calls[
                "update_object"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.update_object,
                default_retry=self._method_configs["UpdateObject"].retry,
                default_timeout=self._method_configs["UpdateObject"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.UpdateObjectRequest(
            bucket=bucket,
            object=object_,
            generation=generation,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
            predefined_acl=predefined_acl,
            projection=projection,
            metadata=api_metadata,
            common_object_request_params=common_object_request_params,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["update_object"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_object_iam_policy(
        self,
        iam_request=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Gets the IAM policy for the specified object.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.get_object_iam_policy()

        Args:
            iam_request (Union[dict, ~google.cloud.storage_v1.types.GetIamPolicyRequest]): The request sent to IAM.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.GetIamPolicyRequest`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Policy` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_object_iam_policy" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_object_iam_policy"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_object_iam_policy,
                default_retry=self._method_configs["GetObjectIamPolicy"].retry,
                default_timeout=self._method_configs["GetObjectIamPolicy"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetIamPolicyRequest(
            iam_request=iam_request, common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_object_iam_policy"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def set_object_iam_policy(
        self,
        iam_request=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates an IAM policy for the specified object.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.set_object_iam_policy()

        Args:
            iam_request (Union[dict, ~google.cloud.storage_v1.types.SetIamPolicyRequest]): The request sent to IAM.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.SetIamPolicyRequest`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Policy` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "set_object_iam_policy" not in self._inner_api_calls:
            self._inner_api_calls[
                "set_object_iam_policy"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.set_object_iam_policy,
                default_retry=self._method_configs["SetObjectIamPolicy"].retry,
                default_timeout=self._method_configs["SetObjectIamPolicy"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.SetIamPolicyRequest(
            iam_request=iam_request, common_request_params=common_request_params,
        )
        return self._inner_api_calls["set_object_iam_policy"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def test_object_iam_permissions(
        self,
        iam_request=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Tests a set of permissions on the given object to see which, if
        any, are held by the caller.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.test_object_iam_permissions()

        Args:
            iam_request (Union[dict, ~google.cloud.storage_v1.types.TestIamPermissionsRequest]): The request sent to IAM.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.TestIamPermissionsRequest`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.TestIamPermissionsResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "test_object_iam_permissions" not in self._inner_api_calls:
            self._inner_api_calls[
                "test_object_iam_permissions"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.test_object_iam_permissions,
                default_retry=self._method_configs["TestObjectIamPermissions"].retry,
                default_timeout=self._method_configs[
                    "TestObjectIamPermissions"
                ].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.TestIamPermissionsRequest(
            iam_request=iam_request, common_request_params=common_request_params,
        )
        return self._inner_api_calls["test_object_iam_permissions"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def watch_all_objects(
        self,
        bucket=None,
        versions=None,
        delimiter=None,
        max_results=None,
        prefix=None,
        include_trailing_delimiter=None,
        page_token=None,
        projection=None,
        channel=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Watch for changes on all objects in a bucket.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> response = client.watch_all_objects()

        Args:
            bucket (str): Name of the bucket in which to look for objects.
            versions (bool): If ``true``, lists all versions of an object as distinct results.
                The default is ``false``. For more information, see `Object
                Versioning <https://cloud.google.com/storage/docs/object-versioning>`__.
            delimiter (str): Returns results in a directory-like mode. ``items`` will contain
                only objects whose names, aside from the ``prefix``, do not contain
                ``delimiter``. Objects whose names, aside from the ``prefix``, contain
                ``delimiter`` will have their name, truncated after the ``delimiter``,
                returned in ``prefixes``. Duplicate ``prefixes`` are omitted.
            max_results (int): Maximum number of ``items`` plus ``prefixes`` to return in a single
                page of responses. As duplicate ``prefixes`` are omitted, fewer total
                results may be returned than requested. The service will use this
                parameter or 1,000 items, whichever is smaller.
            prefix (str): Filter results to objects whose names begin with this prefix.
            include_trailing_delimiter (bool): If true, objects that end in exactly one instance of ``delimiter``
                will have their metadata included in ``items`` in addition to
                ``prefixes``.
            page_token (str): A previously-returned page token representing part of the larger set of
                results to view.
            projection (~google.cloud.storage_v1.types.Projection): Set of properties to return. Defaults to ``NO_ACL``.
            channel (Union[dict, ~google.cloud.storage_v1.types.Channel]): Properties of the channel to be inserted.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.Channel`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.Channel` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "watch_all_objects" not in self._inner_api_calls:
            self._inner_api_calls[
                "watch_all_objects"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.watch_all_objects,
                default_retry=self._method_configs["WatchAllObjects"].retry,
                default_timeout=self._method_configs["WatchAllObjects"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.WatchAllObjectsRequest(
            bucket=bucket,
            versions=versions,
            delimiter=delimiter,
            max_results=max_results,
            prefix=prefix,
            include_trailing_delimiter=include_trailing_delimiter,
            page_token=page_token,
            projection=projection,
            channel=channel,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["watch_all_objects"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_service_account(
        self,
        project_id,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Retrieves the name of a project's Google Cloud Storage service account.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `project_id`:
            >>> project_id = ''
            >>>
            >>> response = client.get_service_account(project_id)

        Args:
            project_id (str): Required. Project ID.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ServiceAccount` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_service_account" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_service_account"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_service_account,
                default_retry=self._method_configs["GetServiceAccount"].retry,
                default_timeout=self._method_configs["GetServiceAccount"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetProjectServiceAccountRequest(
            project_id=project_id, common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_service_account"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def create_hmac_key(
        self,
        project_id,
        service_account_email,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Creates a new HMAC key for the given service account.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `project_id`:
            >>> project_id = ''
            >>>
            >>> # TODO: Initialize `service_account_email`:
            >>> service_account_email = ''
            >>>
            >>> response = client.create_hmac_key(project_id, service_account_email)

        Args:
            project_id (str): Required. The project that the HMAC-owning service account lives in.
            service_account_email (str): Required. The service account to create the HMAC for.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.CreateHmacKeyResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "create_hmac_key" not in self._inner_api_calls:
            self._inner_api_calls[
                "create_hmac_key"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.create_hmac_key,
                default_retry=self._method_configs["CreateHmacKey"].retry,
                default_timeout=self._method_configs["CreateHmacKey"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.CreateHmacKeyRequest(
            project_id=project_id,
            service_account_email=service_account_email,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["create_hmac_key"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def delete_hmac_key(
        self,
        access_id,
        project_id,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Deletes a given HMAC key.  Key must be in an INACTIVE state.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `access_id`:
            >>> access_id = ''
            >>>
            >>> # TODO: Initialize `project_id`:
            >>> project_id = ''
            >>>
            >>> client.delete_hmac_key(access_id, project_id)

        Args:
            access_id (str): Required. The identifying key for the HMAC to delete.
            project_id (str): Required. The project id the HMAC key lies in.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "delete_hmac_key" not in self._inner_api_calls:
            self._inner_api_calls[
                "delete_hmac_key"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.delete_hmac_key,
                default_retry=self._method_configs["DeleteHmacKey"].retry,
                default_timeout=self._method_configs["DeleteHmacKey"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.DeleteHmacKeyRequest(
            access_id=access_id,
            project_id=project_id,
            common_request_params=common_request_params,
        )
        self._inner_api_calls["delete_hmac_key"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def get_hmac_key(
        self,
        access_id,
        project_id,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Gets an existing HMAC key metadata for the given id.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `access_id`:
            >>> access_id = ''
            >>>
            >>> # TODO: Initialize `project_id`:
            >>> project_id = ''
            >>>
            >>> response = client.get_hmac_key(access_id, project_id)

        Args:
            access_id (str): Required. The identifying key for the HMAC to delete.
            project_id (str): Required. The project id the HMAC key lies in.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.HmacKeyMetadata` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "get_hmac_key" not in self._inner_api_calls:
            self._inner_api_calls[
                "get_hmac_key"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.get_hmac_key,
                default_retry=self._method_configs["GetHmacKey"].retry,
                default_timeout=self._method_configs["GetHmacKey"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.GetHmacKeyRequest(
            access_id=access_id,
            project_id=project_id,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["get_hmac_key"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def list_hmac_keys(
        self,
        project_id,
        service_account_email=None,
        show_deleted_keys=None,
        max_results=None,
        page_token=None,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Lists HMAC keys under a given project with the additional filters provided.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `project_id`:
            >>> project_id = ''
            >>>
            >>> response = client.list_hmac_keys(project_id)

        Args:
            project_id (str): Required. The project id to list HMAC keys for.
            service_account_email (str): An optional filter to only return HMAC keys for one service account.
            show_deleted_keys (bool): An optional bool to return deleted keys that have not been wiped out yet.
            max_results (int): The maximum number of keys to return.
            page_token (str): A previously returned token from ListHmacKeysResponse to get the next page.
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.ListHmacKeysResponse` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "list_hmac_keys" not in self._inner_api_calls:
            self._inner_api_calls[
                "list_hmac_keys"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.list_hmac_keys,
                default_retry=self._method_configs["ListHmacKeys"].retry,
                default_timeout=self._method_configs["ListHmacKeys"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.ListHmacKeysRequest(
            project_id=project_id,
            service_account_email=service_account_email,
            show_deleted_keys=show_deleted_keys,
            max_results=max_results,
            page_token=page_token,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["list_hmac_keys"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )

    def update_hmac_key(
        self,
        access_id,
        project_id,
        api_metadata,
        common_request_params=None,
        retry=google.api_core.gapic_v1.method.DEFAULT,
        timeout=google.api_core.gapic_v1.method.DEFAULT,
        metadata=None,
    ):
        """
        Updates a given HMAC key state between ACTIVE and INACTIVE.

        Example:
            >>> from google.cloud import storage_v1
            >>>
            >>> client = storage_v1.StorageClient()
            >>>
            >>> # TODO: Initialize `access_id`:
            >>> access_id = ''
            >>>
            >>> # TODO: Initialize `project_id`:
            >>> project_id = ''
            >>>
            >>> # TODO: Initialize `metadata`:
            >>> metadata = {}
            >>>
            >>> response = client.update_hmac_key(access_id, project_id, metadata)

        Args:
            access_id (str): Required. The id of the HMAC key.
            project_id (str): Required. The project id the HMAC's service account lies in.
            metadata (Union[dict, ~google.cloud.storage_v1.types.HmacKeyMetadata]): Required. The service account owner of the HMAC key.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.HmacKeyMetadata`
            common_request_params (Union[dict, ~google.cloud.storage_v1.types.CommonRequestParams]): A set of parameters common to all Storage API requests.

                If a dict is provided, it must be of the same form as the protobuf
                message :class:`~google.cloud.storage_v1.types.CommonRequestParams`
            retry (Optional[google.api_core.retry.Retry]):  A retry object used
                to retry requests. If ``None`` is specified, requests will
                be retried using a default configuration.
            timeout (Optional[float]): The amount of time, in seconds, to wait
                for the request to complete. Note that if ``retry`` is
                specified, the timeout applies to each individual attempt.
            metadata (Optional[Sequence[Tuple[str, str]]]): Additional metadata
                that is provided to the method.

        Returns:
            A :class:`~google.cloud.storage_v1.types.HmacKeyMetadata` instance.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request
                    failed for any reason.
            google.api_core.exceptions.RetryError: If the request failed due
                    to a retryable error and retry attempts failed.
            ValueError: If the parameters are invalid.
        """
        # Wrap the transport method to add retry and timeout logic.
        if "update_hmac_key" not in self._inner_api_calls:
            self._inner_api_calls[
                "update_hmac_key"
            ] = google.api_core.gapic_v1.method.wrap_method(
                self.transport.update_hmac_key,
                default_retry=self._method_configs["UpdateHmacKey"].retry,
                default_timeout=self._method_configs["UpdateHmacKey"].timeout,
                client_info=self._client_info,
            )

        request = storage_pb2.UpdateHmacKeyRequest(
            access_id=access_id,
            project_id=project_id,
            metadata=api_metadata,
            common_request_params=common_request_params,
        )
        return self._inner_api_calls["update_hmac_key"](
            request, retry=retry, timeout=timeout, metadata=metadata
        )
