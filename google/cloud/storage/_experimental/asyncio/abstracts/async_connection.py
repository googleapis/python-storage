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

"""Abstract class for Async JSON and GRPC connection."""

import abc
from google.cloud.storage._http import AGENT_VERSION
from google.api_core.client_info import ClientInfo
from google.cloud.storage import __version__


class AsyncConnection(abc.ABC):
    """Class for asynchronous connection with JSON and GRPC compatibility.

    This class expose python implementation of interacting with relevant APIs.

    Args:
        client: The client that owns this connection.
        client_info: Information about the client library.
    """

    def __init__(self, client, client_info=None):
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

    @property
    def extra_headers(self):
        """Returns extra headers to send with every request."""
        return self._extra_headers

    @extra_headers.setter
    def extra_headers(self, value):
        """Set the extra header property."""
        self._extra_headers = value

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

    async def close(self):
        pass
