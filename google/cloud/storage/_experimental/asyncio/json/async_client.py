"""Async client for SDK downloads"""

import os
import asyncio
import aiofiles

from google.cloud.storage._experimental.asyncio.json import _helpers
from google.cloud.storage._experimental.asyncio.json import download
from google.cloud.storage._helpers import _DEFAULT_SCHEME
from google.cloud.storage._helpers import _STORAGE_HOST_TEMPLATE
from google.cloud.storage._helpers import _DEFAULT_UNIVERSE_DOMAIN
from google.cloud.storage import blob


_SLICED_DOWNLOAD_THRESHOLD = 1024*1024*1024 # 1GB
_SLICED_DOWNLOAD_PARTS = 5
_USERAGENT = 'test-prototype'


class AsyncClient(_helpers.ClientWithProjectAsync):
    
    SCOPE = (
        "https://www.googleapis.com/auth/devstorage.full_control",
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/devstorage.read_write",
    )

    @property
    def api_endpoint(self):
       return _DEFAULT_SCHEME + _STORAGE_HOST_TEMPLATE.format(
            universe_domain=_DEFAULT_UNIVERSE_DOMAIN
        ) 

    def _get_download_url(self, blob_obj):
        return f'{self.api_endpoint}/download/storage/v1/b/{blob_obj.bucket.name}/o/{blob_obj.name}?alt=media'

    async def _perform_download(
        self,
        transport,
        file_obj,
        download_url,
        headers,
        start=None,
        end=None,
        timeout=None,
        checksum="md5",
        retry=_helpers.DEFAULT_ASYNC_RETRY,
        sequential_read=False,
    ):
        download_obj = download.DownloadAsync(
            download_url,
            stream=file_obj,
            headers=headers,
            start=start,
            end=end,
            checksum=checksum,
            retry=retry,
            sequential_read=sequential_read,
        )
        await download_obj.consume(transport, timeout=timeout)

    def _check_if_sliced_download_is_eligible(self, obj_size, checksum):
        if obj_size < _SLICED_DOWNLOAD_THRESHOLD:
            return False
        # Need to support checksum validations for parallel downloads.
        return checksum==None

    async def download_to_file(
        self,
        blob_obj,
        filename,
        start=None,
        end=None,
        timeout=None,
        checksum="md5",
        retry=_helpers.DEFAULT_ASYNC_RETRY,
        sequential_read=False,
    ):
        download_url = self._get_download_url(blob_obj)
        headers = blob._get_encryption_headers(blob_obj._encryption_key)
        headers["accept-encoding"] = "gzip"
        headers = {
            **blob._get_default_headers(_USERAGENT),
            **headers,
        }

        transport = self._async_http
        if not blob_obj.size:
            blob_obj.reload()
        obj_size = blob_obj.size
        try:
            if not sequential_read and self._check_if_sliced_download_is_eligible(obj_size, checksum): # 1GB
                print("Sliced Download Preferred, and Starting...")
                chunks_offset = [0] + [obj_size//_SLICED_DOWNLOAD_PARTS]*(_SLICED_DOWNLOAD_PARTS-1) + [obj_size - obj_size//_SLICED_DOWNLOAD_PARTS*(_SLICED_DOWNLOAD_PARTS-1)]
                for i in range(1, _SLICED_DOWNLOAD_PARTS+1):
                    chunks_offset[i]+=chunks_offset[i-1]
                
                with open(filename, 'wb') as _: pass # trunacates the file to zero, and keeps the file.
                
                tasks, file_handles = [], []
                try:
                    for idx in range(_SLICED_DOWNLOAD_PARTS):
                        file_handle = await aiofiles.open(filename, 'r+b')
                        await file_handle.seek(chunks_offset[idx])
                        tasks.append(
                            self._perform_download(
                                transport,
                                file_handle,
                                download_url,
                                headers,
                                chunks_offset[idx],
                                chunks_offset[idx+1]-1,
                                timeout=timeout,
                                checksum=checksum,
                                retry=retry,
                                sequential_read=sequential_read,
                            )
                        )
                        file_handles.append(file_handle)
                    await asyncio.gather(*tasks)
                finally:
                    for file_handle in file_handles:
                        await file_handle.close()
            else:
                print("Sequential Download Preferred, and Starting...")
                async with aiofiles.open(filename, "wb") as file_obj:
                    await self._perform_download(
                        transport,
                        file_obj,
                        download_url,
                        headers,
                        start,
                        end,
                        timeout=timeout,
                        checksum=checksum,
                        retry=retry,
                        sequential_read=sequential_read,
                    )
        except (blob.DataCorruption, blob.NotFound):
            await aiofiles.os.remove(filename)
            raise
        except blob.InvalidResponse as exc:
            blob._raise_from_invalid_response(exc)
