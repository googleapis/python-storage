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
"""
NOTE:
This is _experimental module for upcoming support for Rapid Storage.
(https://cloud.google.com/blog/products/storage-data-transfer/high-performance-storage-innovations-for-ai-hpc#:~:text=your%20AI%20workloads%3A-,Rapid%20Storage,-%3A%20A%20new)

APIs may not work as intented and are not stable yet. Feature is not
GA(Generally Available) yet, please contact your TAM(Technical Account Manager)
if you want to use these APIs.

"""

from google.cloud.storage._experimental.asyncio.async_abstract_object_stream import (
    _AsyncAbstractObjectStream,
)


class _AsyncReadObjectStream(_AsyncAbstractObjectStream):
    """Provides an asynchronous, streaming interface for reading from a GCS object.

    This class provides a unix socket-like interface to a GCS Object, with
    methods like ``open``, ``close``, ``send``, and ``recv``.

    :type client: :class:`~google.cloud.storage.aio.Client`
    :param client: The asynchronous client to use for making API requests.

    :type bucket_name: str
    :param bucket_name: The name of the bucket containing the object.

    :type object_name: str
    :param object_name: The name of the object to be read.

    :type generation_number: int
    :param generation_number: (Optional) If present, selects a specific revision of
                              this object.

    :type read_handle: object
    :param read_handle: (Optional) An existing handle for reading the object.
                        If provided, opening the bidi-gRPC connection will be faster.
    """

    def __init__(
        self,
        client,
        bucket_name=None,
        object_name=None,
        generation_number=None,
        read_handle=None,
    ):
        super().__init__(
            bucket_name=bucket_name,
            object_name=object_name,
            generation_number=generation_number,
        )
        self.client = client
        self.read_handle = read_handle

    async def open(self) -> None:
        pass

    async def close(self):
        pass

    async def send(self, bidi_read_object_request):
        pass

    async def recv(self):
        pass
