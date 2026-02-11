"""Async classes for holding the credentials, and connection"""


import google.auth._credentials_async
from google.cloud.client import _ClientProjectMixin
from google.cloud.client import _CREDENTIALS_REFRESH_TIMEOUT
from google.auth.transport import _aiohttp_requests as async_requests
from google.cloud.storage import retry as storage_retry
from google.auth import _default_async
from google.api_core import retry_async


DEFAULT_ASYNC_RETRY = retry_async.AsyncRetry(predicate=storage_retry._should_retry)

class Client:
    SCOPE = None
    # Would be overridden by child classes.

    def __init__(self):
        async_creds, _ = _default_async.default_async(scopes=self.SCOPE)
        self._async_credentials = google.auth._credentials_async.with_scopes_if_required(
            async_creds, scopes=self.SCOPE
        )
        self._async_http_internal = None

    @property
    def _async_http(self):
        if self._async_http_internal is None:
            self._async_http_internal = async_requests.AuthorizedSession(
                self._async_credentials,
                refresh_timeout=_CREDENTIALS_REFRESH_TIMEOUT,
            )
        return self._async_http_internal
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        if self._async_http_internal is not None:
            await self._async_http_internal.close()


class ClientWithProjectAsync(Client, _ClientProjectMixin):
    _SET_PROJECT = True

    def __init__(self, project=None):
        _ClientProjectMixin.__init__(self, project=project)
        Client.__init__(self)