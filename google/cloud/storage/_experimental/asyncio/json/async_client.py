"""Async client for SDK downloads"""

import os
import asyncio
import google.api_core.client_options


from google.auth._credentials_async import AnonymousCredentials
from google.cloud.storage._experimental.asyncio.json import _helpers
from google.cloud.storage._experimental.asyncio.json import download
from google.cloud.storage._helpers import _get_environ_project
from google.cloud.storage._helpers import _get_storage_emulator_override
from google.cloud.storage._helpers import _get_api_endpoint_override
from google.cloud.storage._helpers import _use_client_cert
from google.cloud.storage._helpers import _DEFAULT_SCHEME
from google.cloud.storage._helpers import _STORAGE_HOST_TEMPLATE
from google.cloud.storage._helpers import _DEFAULT_UNIVERSE_DOMAIN
from google.cloud.storage import blob



_marker = object()

class AsyncClient(_helpers.ClientWithProjectAsync):
    
    SCOPE = (
        "https://www.googleapis.com/auth/devstorage.full_control",
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/devstorage.read_write",
    )

    def __init__(
        self,
        project=_marker,
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

        if project is _marker:
            project = None

        self._initial_client_info = client_info
        self._initial_client_options = client_options
        self._extra_headers = extra_headers

        connection_kw_args = {"client_info": client_info}

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

        if client_options and client_options.api_endpoint:
            api_endpoint = client_options.api_endpoint

        elif storage_emulator_override:
            api_endpoint = storage_emulator_override

        elif api_endpoint_override:
            api_endpoint = api_endpoint_override

        elif self._universe_domain:

            if _use_client_cert():
                raise ValueError(
                    'The "GOOGLE_API_USE_CLIENT_CERTIFICATE" env variable is '
                    'set to "true" and a non-default universe domain is '
                    "configured. mTLS is not supported in any universe other than"
                    "googleapis.com."
                )
            api_endpoint = _DEFAULT_SCHEME + _STORAGE_HOST_TEMPLATE.format(
                universe_domain=self._universe_domain
            )

        else:
            api_endpoint = None

        connection_kw_args["api_endpoint"] = api_endpoint

        self._is_emulator_set = True if storage_emulator_override else False

        if connection_kw_args["api_endpoint"] is not None:
            if self._is_emulator_set or not use_auth_w_custom_endpoint:
                if credentials is None:
                    credentials = AnonymousCredentials()
                if project is None:
                    project = _get_environ_project()
                if project is None:
                    no_project = True
                    project = "<none>"

        super(AsyncClient, self).__init__(
            project=project,
            credentials=credentials,
            client_options=client_options,
            _http=_http,
        )


        if self._async_credentials.universe_domain != self.universe_domain:
            raise ValueError(
                "The configured universe domain ({client_ud}) does not match "
                "the universe domain found in the credentials ({cred_ud}). If "
                "you haven't configured the universe domain explicitly, "
                "`googleapis.com` is the default.".format(
                    client_ud=self.universe_domain,
                    cred_ud=self._async_credentials.universe_domain,
                )
            )

        if no_project:
            self.project = None

        connection = _helpers.AsyncConnection(self, **connection_kw_args)
        connection.extra_headers = extra_headers
        self._connection = connection

    @property
    def universe_domain(self):
        return self._universe_domain or _DEFAULT_UNIVERSE_DOMAIN

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
        extra_attributes = blob._get_opentelemetry_attributes_from_url(download_url)
        extra_attributes["upload.checksum"] = f"{checksum}"

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
        if obj_size < 1024*1024*1024:
            return False
        # Need to support checksum validations for parallel downloads.
        return checksum==None

    async def download_to_file(
        self,
        blob_obj,
        filename,
        start=None,
        end=None,
        if_etag_match=None,
        if_etag_not_match=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
        checksum="md5",
        retry=_helpers.DEFAULT_ASYNC_RETRY,
        sequential_read=False,
    ):
        download_url = blob_obj._get_download_url(
            self,
            if_generation_match=if_generation_match,
            if_generation_not_match=if_generation_not_match,
            if_metageneration_match=if_metageneration_match,
            if_metageneration_not_match=if_metageneration_not_match,
        )
        headers = blob._get_encryption_headers(blob_obj._encryption_key)
        headers["accept-encoding"] = "gzip"
        blob._add_etag_match_headers(
            headers,
            if_etag_match=if_etag_match,
            if_etag_not_match=if_etag_not_match,
        )
        headers = {
            **blob._get_default_headers(self._connection.user_agent, command=None),
            **headers,
            **self._extra_headers,
        }

        transport = self._async_http
        if not blob_obj.size:
            blob_obj.reload()
        obj_size = blob_obj.size
        try:
            if not sequential_read and self._check_if_sliced_download_is_eligible(obj_size, checksum): # 1GB
                print("Sliced Download Preferred, and Starting...")
                _parts = 5
                chunks_offset = [0] + [obj_size//_parts]*(_parts-1) + [obj_size - obj_size//_parts*(_parts-1)]
                for i in range(1, _parts+1):
                    chunks_offset[i]+=chunks_offset[i-1]
                
                with open(filename, 'wb') as _: pass # trunacates the file to zero, and keeps the file.
                
                tasks, file_handles = [], []
                try:
                    for idx in range(_parts):
                        file_handle = open(filename, 'r+b')
                        file_handle.seek(chunks_offset[idx])
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
                        file_handle.close()
            else:
                print("Sequential Download Preferred, and Starting...")
                with open(filename, "wb") as file_obj:
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
            os.remove(filename)
            raise
        except blob.InvalidResponse as exc:
            blob._raise_from_invalid_response(exc)
        
        updated = blob_obj.updated
        if updated is not None:
            mtime = updated.timestamp()
            os.utime(filename, (mtime, mtime))