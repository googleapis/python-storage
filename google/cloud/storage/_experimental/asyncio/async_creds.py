"""Async Wrapper around Google Auth Credentials"""

import asyncio
from google.auth.aio import credentials as async_creds
from google.auth.transport.requests import Request

class AsyncCredsWrapper(async_creds.Credentials):
    """Wraps synchronous Google Auth credentials to provide an asynchronous interface.

    This class adapts standard synchronous `google.auth.credentials.Credentials` for use 
    in asynchronous contexts. It offloads blocking operations, such as token refreshes, 
    to a separate thread using `asyncio.loop.run_in_executor`.

    Args:
        sync_creds (google.auth.credentials.Credentials): The synchronous credentials 
            instance to wrap.
    """

    def __init__(self, sync_creds):
        super().__init__()
        self.creds = sync_creds

    async def refresh(self, _request):
        """Refreshes the access token."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.creds.refresh, Request()
        )

    @property
    def valid(self):
        """Checks the validity of the credentials."""
        return self.creds.valid

    async def before_request(self, _request, method, url, headers):
        """Performs credential-specific before request logic."""
        if self.valid:
            self.creds.apply(headers)
            return

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.creds.before_request, Request(), method, url, headers
        )
