"""Async based download code"""

import http
import aiohttp

from google.cloud.storage._experimental.asyncio.json._helpers import DEFAULT_ASYNC_RETRY
from google.cloud.storage._media.requests import _request_helpers
from google.cloud.storage._media import _download
from google.cloud.storage._media import _helpers
from google.cloud.storage._media.requests import download as storage_download


class DownloadAsync(_request_helpers.RequestsMixin, _download.Download):

    def __init__(
        self,
        media_url,
        stream=None,
        start=None,
        end=None,
        headers=None,
        checksum="md5",
        retry=DEFAULT_ASYNC_RETRY,
        sequential_read=False,
    ):
        super().__init__(
            media_url, stream=stream, start=start, end=end, headers=headers, checksum=checksum, retry=retry 
        )
        self.sequential_read = sequential_read

    async def _write_to_stream(self, response):
        if not self.sequential_read:
            # If we've not set expected checksum, or checksum object yet, and if it is not
            # sequential download, API would not return us hash value for each chunk.
            # We could ideally compute the crc32c checksum for each chunk, and later combine them
            # and check, However for prototype not implementing it.
            expected_checksum = None
            checksum_object = _helpers._DoNothingHash()
            self._expected_checksum = expected_checksum
            self._checksum_object = checksum_object
        else:
            # Sequential read, so fetch the hash from the headers.
            expected_checksum, checksum_object = _helpers._get_expected_checksum(
                response, self._get_headers, self.media_url, checksum_type=self.checksum
            )
            self._expected_checksum = expected_checksum
            self._checksum_object = checksum_object

        async with response:
            chunk_size = 4096 * 32
            async for chunk in response.content.iter_chunked(chunk_size):
                await self._stream.write(chunk)
                self._bytes_downloaded += len(chunk)
                checksum_object.update(chunk)

        if (
            expected_checksum is not None
            and response.status != http.client.PARTIAL_CONTENT
        ):
            actual_checksum = _helpers.prepare_checksum_digest(checksum_object.digest())
            
            if actual_checksum != expected_checksum:
                raise storage_download.DataCorruption('Corrupted download!')

    async def consume(
        self,
        transport,
        timeout=aiohttp.ClientTimeout(total=None, sock_read=300),
    ):
        method, _, payload, headers = self._prepare_request()
        request_kwargs = {
            "data": payload,
            "headers": headers,
            "timeout": timeout,
        }
        async def retriable_request():
            url = self.media_url
            result = await transport.request(method, url, **request_kwargs)
            await self._write_to_stream(result)
            if result.status not in (http.client.OK, http.client.PARTIAL_CONTENT):
                result.raise_for_status()
            return result

        return await _request_helpers.wait_and_retry(retriable_request, self._retry_strategy)
