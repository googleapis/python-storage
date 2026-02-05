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

import functools

from google.cloud.storage._experimental.asyncio.async_helpers import (
    ASYNC_DEFAULT_TIMEOUT,
)
from google.cloud.storage._experimental.asyncio.async_helpers import ASYNC_DEFAULT_RETRY
from google.cloud.storage._experimental.asyncio.async_helpers import AsyncHTTPIterator
from google.cloud.storage._experimental.asyncio.async_helpers import (
    _do_nothing_page_start,
)
from google.cloud.storage._opentelemetry_tracing import create_trace_span
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
            api_key=api_key,
        )
        self.credentials = AsyncCredsWrapper(
            self._credentials
        )  # self._credential is synchronous.
        self._connection = AsyncConnection(
            self, **self.connection_kw_args
        )  # adapter for async communication
        self._async_http_internal = _async_http
        self._async_http_passed_by_user = _async_http is not None

    @property
    def async_http(self):
        """Returns the existing asynchronous session, or create one if it does not exists."""
        if self._async_http_internal is None:
            self._async_http_internal = AsyncSession(credentials=self.credentials)
        return self._async_http_internal

    async def close(self):
        """Close the session, if it exists"""
        if (
            self._async_http_internal is not None
            and not self._async_http_passed_by_user
        ):
            await self._async_http_internal.close()

    async def _get_resource(
        self,
        path,
        query_params=None,
        headers=None,
        timeout=ASYNC_DEFAULT_TIMEOUT,
        retry=ASYNC_DEFAULT_RETRY,
        _target_object=None,
    ):
        """See super() class"""
        return await self._connection.api_request(
            method="GET",
            path=path,
            query_params=query_params,
            headers=headers,
            timeout=timeout,
            retry=retry,
            _target_object=_target_object,
        )

    def _list_resource(
        self,
        path,
        item_to_value,
        page_token=None,
        max_results=None,
        extra_params=None,
        page_start=_do_nothing_page_start,
        page_size=None,
        timeout=ASYNC_DEFAULT_TIMEOUT,
        retry=ASYNC_DEFAULT_RETRY,
    ):
        """See super() class"""
        kwargs = {
            "method": "GET",
            "path": path,
            "timeout": timeout,
        }
        with create_trace_span(
            name="Storage.AsyncClient._list_resource_returns_iterator",
            client=self,
            api_request=kwargs,
            retry=retry,
        ):
            api_request = functools.partial(
                self._connection.api_request, timeout=timeout, retry=retry
            )
        return AsyncHTTPIterator(
            client=self,
            api_request=api_request,
            path=path,
            item_to_value=item_to_value,
            page_token=page_token,
            max_results=max_results,
            extra_params=extra_params,
            page_start=page_start,
            page_size=page_size,
        )

    async def _patch_resource(
        self,
        path,
        data,
        query_params=None,
        headers=None,
        timeout=ASYNC_DEFAULT_TIMEOUT,
        retry=None,
        _target_object=None,
    ):
        """See super() class"""
        return await self._connection.api_request(
            method="PATCH",
            path=path,
            data=data,
            query_params=query_params,
            headers=headers,
            timeout=timeout,
            retry=retry,
            _target_object=_target_object,
        )

    async def _put_resource(
        self,
        path,
        data,
        query_params=None,
        headers=None,
        timeout=ASYNC_DEFAULT_TIMEOUT,
        retry=None,
        _target_object=None,
    ):
        """See super() class"""
        return await self._connection.api_request(
            method="PUT",
            path=path,
            data=data,
            query_params=query_params,
            headers=headers,
            timeout=timeout,
            retry=retry,
            _target_object=_target_object,
        )

    async def _post_resource(
        self,
        path,
        data,
        query_params=None,
        headers=None,
        timeout=ASYNC_DEFAULT_TIMEOUT,
        retry=None,
        _target_object=None,
    ):
        """See super() class"""
        return await self._connection.api_request(
            method="POST",
            path=path,
            data=data,
            query_params=query_params,
            headers=headers,
            timeout=timeout,
            retry=retry,
            _target_object=_target_object,
        )

    async def _delete_resource(
        self,
        path,
        query_params=None,
        headers=None,
        timeout=ASYNC_DEFAULT_TIMEOUT,
        retry=ASYNC_DEFAULT_RETRY,
        _target_object=None,
    ):
        """See super() class"""
        return await self._connection.api_request(
            method="DELETE",
            path=path,
            query_params=query_params,
            headers=headers,
            timeout=timeout,
            retry=retry,
            _target_object=_target_object,
        )

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
