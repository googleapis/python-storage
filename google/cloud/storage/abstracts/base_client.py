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
"""The abstract for python-storage Client."""

from google.cloud.storage._helpers import _get_api_endpoint_override
from google.cloud.storage._helpers import _get_environ_project
from google.cloud.storage._helpers import _get_storage_emulator_override
from google.cloud.storage._helpers import _DEFAULT_SCHEME
from google.cloud.storage._helpers import _STORAGE_HOST_TEMPLATE
from google.auth.credentials import AnonymousCredentials
from google.cloud.storage._helpers import _DEFAULT_UNIVERSE_DOMAIN
from google.cloud.client import ClientWithProject
from google.cloud._helpers import _LocalStack
from google.auth.transport import mtls
from abc import ABC, abstractmethod

import os
import google.api_core.client_options

marker = object()

class BaseClient(ClientWithProject, ABC):
    """Abstract class for python-storage Client"""

    SCOPE = (
        "https://www.googleapis.com/auth/devstorage.full_control",
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/devstorage.read_write",
    )
    """The scopes required for authenticating as a Cloud Storage consumer."""

    def __init__(
        self,
        project=marker,
        credentials=None,
        _http=None,
        client_info=None,
        client_options=None,
        use_auth_w_custom_endpoint=True,
        extra_headers={},
        *,
        api_key=None,
    ):
        self._base_connection = None

        if project is None:
            no_project = True
            project = "<none>"
        else:
            no_project = False

        if project is marker:
            project = None

        # Save the initial value of constructor arguments before they
        # are passed along, for use in __reduce__ defined elsewhere.
        self._initial_client_info = client_info
        self._initial_client_options = client_options
        self._extra_headers = extra_headers

        connection_kw_args = {"client_info": client_info}

        # api_key should set client_options.api_key. Set it here whether
        # client_options was specified as a dict, as a ClientOptions object, or
        # None.
        if api_key:
            if client_options and not isinstance(client_options, dict):
                client_options.api_key = api_key
            else:
                if not client_options:
                    client_options = {}
                client_options["api_key"] = api_key

        if client_options:
            if isinstance(client_options, dict):
                client_options = google.api_core.client_options.from_dict(
                    client_options
                )

        if client_options and client_options.universe_domain:
            self._universe_domain = client_options.universe_domain
        else:
            self._universe_domain = None

        storage_emulator_override = _get_storage_emulator_override()
        api_endpoint_override = _get_api_endpoint_override()

        # Determine the api endpoint. The rules are as follows:

        # 1. If the `api_endpoint` is set in `client_options`, use that as the
        #    endpoint.
        if client_options and client_options.api_endpoint:
            api_endpoint = client_options.api_endpoint

        # 2. Elif the "STORAGE_EMULATOR_HOST" env var is set, then use that as the
        #    endpoint.
        elif storage_emulator_override:
            api_endpoint = storage_emulator_override

        # 3. Elif the "API_ENDPOINT_OVERRIDE" env var is set, then use that as the
        #    endpoint.
        elif api_endpoint_override:
            api_endpoint = api_endpoint_override

        # 4. Elif the `universe_domain` is set in `client_options`,
        #    create the endpoint using that as the default.
        #
        #    Mutual TLS is not compatible with a non-default universe domain
        #    at this time. If such settings are enabled along with the
        #    "GOOGLE_API_USE_CLIENT_CERTIFICATE" env variable, a ValueError will
        #    be raised.

        elif self._universe_domain:
            # The final decision of whether to use mTLS takes place in
            # google-auth-library-python. We peek at the environment variable
            # here only to issue an exception in case of a conflict.
            use_client_cert = False
            if hasattr(mtls, "should_use_client_cert"):
                use_client_cert = mtls.should_use_client_cert()
            else:
                use_client_cert = (
                    os.getenv("GOOGLE_API_USE_CLIENT_CERTIFICATE") == "true"
                )

            if use_client_cert:
                raise ValueError(
                    'The "GOOGLE_API_USE_CLIENT_CERTIFICATE" env variable is '
                    'set to "true" and a non-default universe domain is '
                    "configured. mTLS is not supported in any universe other than"
                    "googleapis.com."
                )
            api_endpoint = _DEFAULT_SCHEME + _STORAGE_HOST_TEMPLATE.format(
                universe_domain=self._universe_domain
            )

        # 5. Else, use the default, which is to use the default
        #    universe domain of "googleapis.com" and create the endpoint
        #    "storage.googleapis.com" from that.
        else:
            api_endpoint = None

        connection_kw_args["api_endpoint"] = api_endpoint
        self._is_emulator_set = True if storage_emulator_override else False

        # If a custom endpoint is set, the client checks for credentials
        # or finds the default credentials based on the current environment.
        # Authentication may be bypassed under certain conditions:
        # (1) STORAGE_EMULATOR_HOST is set (for backwards compatibility), OR
        # (2) use_auth_w_custom_endpoint is set to False.
        if connection_kw_args["api_endpoint"] is not None:
            if self._is_emulator_set or not use_auth_w_custom_endpoint:
                if credentials is None:
                    credentials = AnonymousCredentials()
                if project is None:
                    project = _get_environ_project()
                if project is None:
                    no_project = True
                    project = "<none>"

        super(BaseClient, self).__init__(
            project=project,
            credentials=credentials,
            client_options=client_options,
            _http=_http,
        )

        # Validate that the universe domain of the credentials matches the
        # universe domain of the client.
        if self._credentials.universe_domain != self.universe_domain:
            raise ValueError(
                "The configured universe domain ({client_ud}) does not match "
                "the universe domain found in the credentials ({cred_ud}). If "
                "you haven't configured the universe domain explicitly, "
                "`googleapis.com` is the default.".format(
                    client_ud=self.universe_domain,
                    cred_ud=self._credentials.universe_domain,
                )
            )

        if no_project:
            self.project = None

        self.connection_kw_args = connection_kw_args
        self._batch_stack = _LocalStack()

    @property
    def universe_domain(self):
        return self._universe_domain or _DEFAULT_UNIVERSE_DOMAIN

    @classmethod
    def create_anonymous_client(cls):
        """Factory: return client with anonymous credentials.

        .. note::

           Such a client has only limited access to "public" buckets:
           listing their contents and downloading their blobs.

        :rtype: :class:`google.cloud.storage.client.Client`
        :returns: Instance w/ anonymous credentials and no project.
        """
        client = cls(project="<none>", credentials=AnonymousCredentials())
        client.project = None
        return client

    @property
    def api_endpoint(self):
        """Returns the API_BASE_URL from connection"""
        return self._connection.API_BASE_URL

    def update_user_agent(self, user_agent):
        """Update the user-agent string for this client.

        :type user_agent: str
        :param user_agent: The string to add to the user-agent.
        """
        existing_user_agent = self._connection._client_info.user_agent
        if existing_user_agent is None:
            self._connection.user_agent = user_agent
        else:
            self._connection.user_agent = f"{user_agent} {existing_user_agent}"

    @property
    def _connection(self):
        """Get connection or batch on the client.

        :rtype: :class:`google.cloud.storage._http.Connection`
        :returns: The connection set on the client, or the batch
                  if one is set.
        """
        if self.current_batch is not None:
            return self.current_batch
        else:
            return self._base_connection

    @_connection.setter
    def _connection(self, value):
        """Set connection on the client.

        Intended to be used by constructor (since the base class calls)
            self._connection = connection
        Will raise if the connection is set more than once.

        :type value: :class:`google.cloud.storage._http.Connection`
        :param value: The connection set on the client.

        :raises: :class:`ValueError` if connection has already been set.
        """
        if self._base_connection is not None:
            raise ValueError("Connection already set on client")
        self._base_connection = value

    def _push_batch(self, batch):
        """Push a batch onto our stack.

        "Protected", intended for use by batch context mgrs.

        :type batch: :class:`google.cloud.storage.batch.Batch`
        :param batch: newly-active batch
        """
        self._batch_stack.push(batch)

    def _pop_batch(self):
        """Pop a batch from our stack.

        "Protected", intended for use by batch context mgrs.

        :raises: IndexError if the stack is empty.
        :rtype: :class:`google.cloud.storage.batch.Batch`
        :returns: the top-most batch/transaction, after removing it.
        """
        return self._batch_stack.pop()

    @property
    def current_batch(self):
        """Currently-active batch.

        :rtype: :class:`google.cloud.storage.batch.Batch` or ``NoneType`` (if
                no batch is active).
        :returns: The batch at the top of the batch stack.
        """
        return self._batch_stack.top

    @abstractmethod
    def bucket(self, bucket_name, user_project=None, generation=None):
        raise NotImplementedError("This method needs to be implemented.")

    @abstractmethod
    def _get_resource(
        self,
        path,
        query_params=None,
        headers=None,
        timeout=None,
        retry=None,
        _target_object=None,
    ):
        """Helper for bucket / blob methods making API 'GET' calls."""
        raise NotImplementedError("This should be implemented via the child class")

    @abstractmethod
    def _list_resource(
        self,
        path,
        item_to_value,
        page_token=None,
        max_results=None,
        extra_params=None,
        page_start=None,
        page_size=None,
        timeout=None,
        retry=None,
    ):
        """Helper for bucket / blob methods making API 'GET' calls."""
        raise NotImplementedError("This should be implemented via the child class")

    @abstractmethod
    def _patch_resource(
        self,
        path,
        data,
        query_params=None,
        headers=None,
        timeout=None,
        retry=None,
        _target_object=None,
    ):
        """Helper for bucket / blob methods making API 'PATCH' calls."""
        raise NotImplementedError("This should be implemented via the child class")

    @abstractmethod
    def _put_resource(
        self,
        path,
        data,
        query_params=None,
        headers=None,
        timeout=None,
        retry=None,
        _target_object=None,
    ):
        """Helper for bucket / blob methods making API 'PUT' calls."""
        raise NotImplementedError("This should be implemented via the child class")

    @abstractmethod
    def _post_resource(
        self,
        path,
        data,
        query_params=None,
        headers=None,
        timeout=None,
        retry=None,
        _target_object=None,
    ):
        """Helper for bucket / blob methods making API 'POST' calls."""
        raise NotImplementedError("This should be implemented via the child class")

    @abstractmethod
    def _delete_resource(
        self,
        path,
        query_params=None,
        headers=None,
        timeout=None,
        retry=None,
        _target_object=None,
    ):
        """Helper for bucket / blob methods making API 'DELETE' calls."""
        raise NotImplementedError("This should be implemented via the child class")
