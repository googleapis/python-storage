# Copyright 2025 Google LLC
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

"""Create/interact with Google Cloud Storage connections in asynchronous manner."""

import json
import collections
import functools
from urllib.parse import urlencode

import google.api_core.exceptions
from google.cloud import _http
from google.cloud.storage import _http as storage_http
from google.cloud.storage import _helpers
from google.api_core.client_info import ClientInfo
from google.cloud.storage._opentelemetry_tracing import create_trace_span
from google.cloud.storage import __version__
from google.cloud.storage._http import AGENT_VERSION


class AsyncConnection:
    """Class for asynchronous connection using google.auth.aio.

    This class handles the creation of API requests, header management,
    user agent configuration, and error handling for the Async Storage Client.

    Args:
        client: The client that owns this connection.
        client_info: Information about the client library.
        api_endpoint: The API endpoint to use.
    """

    def __init__(self, client, client_info=None, api_endpoint=None):
        self._client = client

        if client_info is None:
            client_info = ClientInfo()

        self._client_info = client_info
        if self._client_info.user_agent is None:
            self._client_info.user_agent = AGENT_VERSION
        else:
            self._client_info.user_agent = (
                f"{self._client_info.user_agent} {AGENT_VERSION}"
            )
        self._client_info.client_library_version = __version__
        self._extra_headers = {}

        self.API_BASE_URL = api_endpoint or storage_http.Connection.DEFAULT_API_ENDPOINT
        self.API_VERSION = storage_http.Connection.API_VERSION
        self.API_URL_TEMPLATE = storage_http.Connection.API_URL_TEMPLATE

    @property
    def extra_headers(self):
        """Returns extra headers to send with every request."""
        return self._extra_headers

    @extra_headers.setter
    def extra_headers(self, value):
        """Set the extra header property."""
        self._extra_headers = value

    @property
    def async_http(self):
        """Returns the AsyncAuthorizedSession from the client.

        Returns:
            google.auth.aio.transport.sessions.AsyncAuthorizedSession: The async session.
        """
        return self._client.async_http

    @property
    def user_agent(self):
        """Returns user_agent for async HTTP transport.

        Returns:
            str: The user agent string.
        """
        return self._client_info.to_user_agent()

    @user_agent.setter
    def user_agent(self, value):
        """Setter for user_agent in connection."""
        self._client_info.user_agent = value

    async def _make_request(
        self,
        method,
        url,
        data=None,
        content_type=None,
        headers=None,
        target_object=None,
        timeout=_http._DEFAULT_TIMEOUT,
        extra_api_info=None,
    ):
        """A low level method to send a request to the API.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST').
            url (str): The specific API URL.
            data (Optional[Union[str, bytes, dict]]): The body of the request.
            content_type (Optional[str]): The Content-Type header.
            headers (Optional[dict]): Additional headers for the request.
            target_object (Optional[object]): (Unused in async impl) Reference to the target object.
            timeout (Optional[float]): The timeout in seconds.
            extra_api_info (Optional[str]): Extra info for the User-Agent / Client-Info.

        Returns:
            google.auth.aio.transport.Response: The HTTP response object.
        """
        headers = headers.copy() if headers else {}
        headers.update(self.extra_headers)
        headers["Accept-Encoding"] = "gzip"

        if content_type:
            headers["Content-Type"] = content_type

        if extra_api_info:
            headers[_http.CLIENT_INFO_HEADER] = f"{self.user_agent} {extra_api_info}"
        else:
            headers[_http.CLIENT_INFO_HEADER] = self.user_agent
        headers["User-Agent"] = self.user_agent

        return await self._do_request(
            method, url, headers, data, target_object, timeout=timeout
        )

    async def _do_request(
        self, method, url, headers, data, target_object, timeout=_http._DEFAULT_TIMEOUT
    ):
        """Low-level helper: perform the actual API request.

        Args:
            method (str): HTTP method.
            url (str): API URL.
            headers (dict): HTTP headers.
            data (Optional[bytes]): Request body.
            target_object: Unused in this implementation, kept for compatibility.
            timeout (float): Request timeout.

        Returns:
            google.auth.aio.transport.Response: The response object.
        """
        return await self.async_http.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=timeout,
        )

    async def api_request(self, *args, **kwargs):
        """Perform an API request with retry and tracing support.

        Args:
            *args: Positional arguments passed to _perform_api_request.
            **kwargs: Keyword arguments passed to _perform_api_request.
                Can include 'retry' (an AsyncRetry object).

        Returns:
            Union[dict, bytes]: The parsed JSON response or raw bytes.
        """
        retry = kwargs.pop("retry", None)
        invocation_id = _helpers._get_invocation_id()
        kwargs["extra_api_info"] = invocation_id
        span_attributes = {
            "gccl-invocation-id": invocation_id,
        }

        call = functools.partial(self._perform_api_request, *args, **kwargs)

        with create_trace_span(
            name="Storage.AsyncConnection.api_request",
            attributes=span_attributes,
            client=self._client,
            api_request=kwargs,
            retry=retry,
        ):
            if retry:
                # Ensure the retry policy checks its conditions
                try:
                    retry = retry.get_retry_policy_if_conditions_met(**kwargs)
                except AttributeError:
                    pass
                if retry:
                    call = retry(call)
            return await call()

    def build_api_url(
        self, path, query_params=None, api_base_url=None, api_version=None
    ):
        """Construct an API URL.

        Args:
            path (str): The API path (e.g. '/b/bucket-name').
            query_params (Optional[Union[dict, list]]): Query parameters.
            api_base_url (Optional[str]): Base URL override.
            api_version (Optional[str]): API version override.

        Returns:
            str: The fully constructed URL.
        """
        url = self.API_URL_TEMPLATE.format(
            api_base_url=(api_base_url or self.API_BASE_URL),
            api_version=(api_version or self.API_VERSION),
            path=path,
        )

        query_params = query_params or {}

        if isinstance(query_params, collections.abc.Mapping):
            query_params = query_params.copy()
        else:
            query_params_dict = collections.defaultdict(list)
            for key, value in query_params:
                query_params_dict[key].append(value)
            query_params = query_params_dict

        query_params.setdefault("prettyPrint", "false")

        url += "?" + urlencode(query_params, doseq=True)

        return url

    async def _perform_api_request(
        self,
        method,
        path,
        query_params=None,
        data=None,
        content_type=None,
        headers=None,
        api_base_url=None,
        api_version=None,
        expect_json=True,
        _target_object=None,
        timeout=_http._DEFAULT_TIMEOUT,
        extra_api_info=None,
    ):
        """Internal helper to prepare the URL/Body and execute the request.

        This method handles JSON serialization of the body, URL construction,
        and converts HTTP errors into google.api_core.exceptions.

        Args:
            method (str): HTTP method.
            path (str): URL path.
            query_params (Optional[dict]): Query params.
            data (Optional[Union[dict, bytes]]): Request body.
            content_type (Optional[str]): Content-Type header.
            headers (Optional[dict]): HTTP headers.
            api_base_url (Optional[str]): Base URL override.
            api_version (Optional[str]): API version override.
            expect_json (bool): If True, parses response as JSON. Defaults to True.
            _target_object: Internal use (unused here).
            timeout (float): Request timeout.
            extra_api_info (Optional[str]): Extra client info.

        Returns:
            Union[dict, bytes]: Parsed JSON or raw bytes.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the API returns an error.
        """
        url = self.build_api_url(
            path=path,
            query_params=query_params,
            api_base_url=api_base_url,
            api_version=api_version,
        )

        if data and isinstance(data, dict):
            data = json.dumps(data)
            content_type = "application/json"

        response = await self._make_request(
            method=method,
            url=url,
            data=data,
            content_type=content_type,
            headers=headers,
            target_object=_target_object,
            timeout=timeout,
            extra_api_info=extra_api_info,
        )

        # Handle API Errors
        if not (200 <= response.status_code < 300):
            content = await response.read()
            payload = {}
            if content:
                try:
                    payload = json.loads(content.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    payload = {
                        "error": {"message": content.decode("utf-8", errors="replace")}
                    }
            raise google.api_core.exceptions.format_http_response_error(
                response, method, url, payload
            )

        # Handle Success
        payload = await response.read()
        if expect_json:
            if not payload:
                return {}
            return json.loads(payload)
        else:
            return payload
