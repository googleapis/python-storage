# Copyright 2026 Google LLC
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

"""Asynchronous client for interacting with Google Cloud Storage."""

from google.cloud.storage._experimental.asyncio.async_creds import AsyncCredsWrapper
from google.cloud.storage.abstracts.base_client import BaseClient
from google.cloud.storage._experimental.asyncio.utility.async_json_connection import (
    AsyncJSONConnection,
)
from google.cloud.storage.abstracts import base_client

_marker = base_client.marker


class AsyncClient(BaseClient):
    """Asynchronous client to interact with Google Cloud Storage."""

    def __init__(
        self,
        project=_marker,
        credentials=None,
        _async_http=None,
        client_info=None,
        client_options=None,
        extra_headers={},
        *,
        api_key=None,
    ):
        if self._use_client_cert:
            # google.auth.aio.transports.sessions.AsyncAuthorizedSession currently doesn't support configuring mTLS.
            # In future, we can monkey patch the above, and do provide mTLS support, but that is not a priority
            # at the moment.
            raise ValueError("Async Client currently do not support mTLS")

        # We initialize everything as per synchronous client.
        super().__init__(
            project=project,
            credentials=credentials,
            client_info=client_info,
            client_options=client_options,
            extra_headers=extra_headers,
            api_key=api_key,
        )
        self.credentials = AsyncCredsWrapper(
            self._credentials
        )  # self._credential is synchronous.
        self._async_http = _async_http

        # We need both, as the same client can be used for multiple buckets.
        self._json_connection_internal = None
        self._grpc_connection_internal = None

    @property
    def _grpc_connection(self):
        raise NotImplementedError("Not yet Implemented.")

    @property
    def _json_connection(self):
        if not self._json_connection_internal:
            self._json_connection_internal = AsyncJSONConnection(
                self,
                _async_http=self._async_http,
                credentials=self.credentials,
                **self.connection_kw_args,
            )
        return self._json_connection_internal

    async def close(self):
        if self._json_connection_internal:
            await self._json_connection_internal.close()

        if self._grpc_connection_internal:
            await self._grpc_connection_internal.close()

    def bucket(self, bucket_name, user_project=None, generation=None):
        """Factory constructor for bucket object.

        .. note::
          This will not make an HTTP request; it simply instantiates
          a bucket object owned by this client.

        :type bucket_name: str
        :param bucket_name: The name of the bucket to be instantiated.

        :type user_project: str
        :param user_project: (Optional) The project ID to be billed for API
                             requests made via the bucket.

        :type generation: int
        :param generation: (Optional) If present, selects a specific revision of
                           this bucket.

        :rtype: :class:`google.cloud.storage._experimental.asyncio.bucket.AsyncBucket`
        :returns: The bucket object created.
        """
        raise NotImplementedError("This AsyncBucket class needs to be implemented.")
