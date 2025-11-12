"""Async classes for holding the credentials, and connection"""


import os
import google.api_core

from google.cloud.client import _ClientProjectMixin
from google.cloud.client import _CREDENTIALS_REFRESH_TIMEOUT
from google.cloud.client import _GOOGLE_AUTH_CREDENTIALS_HELP
from google.auth.transport import _aiohttp_requests as async_requests
from google.cloud.storage import retry as storage_retry
from pickle import PicklingError
from google.auth import _default_async
from google.cloud.storage import _http
from google.api_core import retry_async


DEFAULT_ASYNC_RETRY = retry_async.AsyncRetry(predicate=storage_retry._should_retry)

# While the parent class is synchronous, we know that downloads does not use any synchronous network calls
# originated from this class. We still require some helper methods from the parent, so we are keeping the class
# structure as is, with minimal modifications.
class AsyncConnection(_http.Connection):    
    def get_api_base_url_for_mtls(self, api_base_url=None):
        if api_base_url:
            return api_base_url

        env = os.getenv("GOOGLE_API_USE_MTLS_ENDPOINT", "auto")
        if env == "always":
            url_to_use = self.API_BASE_MTLS_URL
        elif env == "never":
            url_to_use = self.API_BASE_URL
        else:
            if self.ALLOW_AUTO_SWITCH_TO_MTLS_URL:
                url_to_use = (
                    self.API_BASE_MTLS_URL if self._client._async_http._is_mtls else self.API_BASE_URL
                )
            else:
                url_to_use = self.API_BASE_URL
        return url_to_use 


class Client:
    SCOPE = None

    def __init__(self, credentials=None, _http=None, client_options=None):
        if isinstance(client_options, dict):
            client_options = google.api_core.client_options.from_dict(client_options)
        if client_options is None:
            client_options = google.api_core.client_options.ClientOptions()

        if credentials and client_options.credentials_file:
            raise google.api_core.exceptions.DuplicateCredentialArgs(
                "'credentials' and 'client_options.credentials_file' are mutually exclusive."
            )

        if client_options.api_key:
            raise ValueError("'client_options.api_key' currently not supported in async version.")

        if credentials and not isinstance(
            credentials, google.auth._credentials_async.Credentials
        ):
            raise ValueError(_GOOGLE_AUTH_CREDENTIALS_HELP)

        scopes = client_options.scopes or self.SCOPE

        if not _http and credentials is None:
            if client_options.credentials_file:
                async_creds, _ = _default_async.load_credentials_from_file(
                    client_options.credentials_file, scopes=scopes
                )
            else:
                # This particular google.auth._default_async.default_async falls back to sync credentials in case of
                # ComputeEngineCredentials, for experimentation - one need to do `gcloud auth application-default login`
                # to ensure that credential do not fall back to Compute Engine.
                async_creds, _ = _default_async.default_async(scopes=scopes)
        else:
            async_creds = credentials

        self._async_credentials = google.auth._credentials_async.with_scopes_if_required(
            async_creds, scopes=scopes
        )

        if client_options.quota_project_id:
            self._async_credentials = self._async_credentials.with_quota_project(
                client_options.quota_project_id
            )

        self._async_http_internal = _http
        self._client_cert_source = client_options.client_cert_source

    def __getstate__(self):
        raise PicklingError(
            "\n".join(
                [
                    "Pickling client objects is explicitly not supported.",
                    "Clients have non-trivial state that is local and unpickleable.",
                ]
            )
        )

    @property
    def _async_http(self):
        if self._async_http_internal is None:
            self._async_http_internal = async_requests.AuthorizedSession(
                self._async_credentials,
                refresh_timeout=_CREDENTIALS_REFRESH_TIMEOUT,
            )
            # self._async_http_internal.configure_mtls_channel(self._client_cert_source)
        return self._async_http_internal
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        del exc_type, exc_val, exc_tb
        if self._async_http_internal is not None:
            await self._async_http_internal.close()


class ClientWithProjectAsync(Client, _ClientProjectMixin):
    _SET_PROJECT = True

    def __init__(self, project=None, credentials=None, client_options=None, _http=None):
        _ClientProjectMixin.__init__(self, project=project, credentials=credentials)
        Client.__init__(
            self, credentials=credentials, client_options=client_options, _http=_http
        )