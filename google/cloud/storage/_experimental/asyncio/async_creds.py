"""Async Wrapper around Google Auth Credentials"""

import asyncio
from google.auth.transport.requests import Request

try:
    from google.auth.aio import credentials as aio_creds_module

    BaseCredentials = aio_creds_module.Credentials
    _AIO_AVAILABLE = True
except ImportError:
    BaseCredentials = object
    _AIO_AVAILABLE = False


class AsyncCredsWrapper(BaseCredentials):
    """Wraps synchronous Google Auth credentials to provide an asynchronous interface.

    Args:
        sync_creds (google.auth.credentials.Credentials): The synchronous credentials
            instance to wrap.

    Raises:
        ImportError: If instantiated in an environment where 'google.auth.aio'
                     is not available.
    """

    def __init__(self, sync_creds):
        if not _AIO_AVAILABLE:
            raise ImportError(
                "Failed to import 'google.auth.aio'. This module requires a newer version "
                "of 'google-auth' which supports asyncio."
            )

        super().__init__()
        self.creds = sync_creds

    async def refresh(self, request):
        """Refreshes the access token."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.creds.refresh, Request())

    @property
    def valid(self):
        """Checks the validity of the credentials."""
        return self.creds.valid

    async def before_request(self, request, method, url, headers):
        """Performs credential-specific before request logic."""
        if self.valid:
            self.creds.apply(headers)
            return

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.creds.before_request, Request(), method, url, headers
        )
