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
from google.cloud.storage._experimental.asyncio.async_connection import AsyncConnection
from google.cloud.storage.abstracts import base_client

try:
    from google.auth.aio.transport import sessions
    AsyncSession = sessions.AsyncAuthorizedSession
    _AIO_AVAILABLE = True
except ImportError:
    _AIO_AVAILABLE = False

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
        if not _AIO_AVAILABLE:
            # Python 3.9 or less comes with an older version of google-auth library which doesn't support asyncio
            raise ImportError(
                "Failed to import 'google.auth.aio', Consider using a newer python version (>=3.10)"
                " or newer version of google-auth library to mitigate this issue."
            )

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
            api_key=api_key
        )
        self.credentials = AsyncCredsWrapper(self._credentials) # self._credential is synchronous.
        self._connection = AsyncConnection(self, **self.connection_kw_args) # adapter for async communication
        self._async_http_internal = _async_http
        self._async_http_passed_by_user = (_async_http is not None)

    @property
    def async_http(self):
        """Returns the existing asynchronous session, or create one if it does not exists."""
        if self._async_http_internal is None:
            self._async_http_internal = AsyncSession(credentials=self.credentials)
        return self._async_http_internal

    async def close(self):
        """Close the session, if it exists"""
        if self._async_http_internal is not None and not self._async_http_passed_by_user:
            await self._async_http_internal.close()


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
