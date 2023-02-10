# Copyright 2017 Google Inc.
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

"""``requests`` utilities for Google Cloud Storage Resumable Media Downloads and Uploads.

This sub-package assumes callers will use the `requests`_ library
as transport and `google-auth`_ for sending authenticated HTTP traffic
with ``requests``.

.. _requests: http://docs.python-requests.org/
.. _google-auth: https://google-auth.readthedocs.io/

The main concepts include:

- :class:`~google.cloud.storage.resumable_media.requests.Download`
  is used to download an object from Google Cloud Storage, construct the media URL
  for the GCS object and download it with an authorized transport that has
  access to the resource.

- :class:`~google.cloud.storage.resumable_media.requests.ChunkedDownload`
  is used to download an object in chunks rather than all at once.
  This can be done to avoid dropped connections with a poor internet connection or can allow
  multiple chunks to be downloaded in parallel to speed up the total
  download.

- :class:`~google.cloud.storage.resumable_media.requests.SimpleUpload`
  is used to upload an object to Google Cloud Storage when the resource being uploaded
  is small and when there is no metadata (other than the name) associated with the resource.

- :class:`~google.cloud.storage.resumable_media.requests.MultipartUpload`
  is used to upload an object to Google Cloud Storage when allowing some
  metadata about the resource to be sent along as well. (This is the "multi":
  we send a first part with the metadata and a second part with the actual
  bytes in the resource.)

- :class:`~google.cloud.storage.resumable_media.requests.ResumableUpload`
  deviates from the other two upload classes. Resumable uploads transmit a resource over
  the course of multiple requests. This is intended to be used in cases where:
  the size of the resource is not known (i.e. it is generated on the fly), the resource is
  too large to fit into memory, requests must be short-lived, or the client has
  request **size** limitations, etc. See `GCS best practices`_ for more things to
  consider when using a resumable upload.

  After creating a :class:`.ResumableUpload` instance, a
  **resumable upload session** must be initiated to let the server know that
  a series of chunked upload requests will be coming and to obtain an
  ``upload_id`` for the session. In contrast to the other two upload classes,
  :meth:`~.ResumableUpload.initiate` takes a byte ``stream`` as input rather
  than raw bytes as ``data``. This can be a file object, a :class:`~io.BytesIO`
  object or any other stream implementing the same interface.

.. _GCS best practices: https://cloud.google.com/storage/docs/\
                        best-practices#uploading
"""

from google.cloud.storage.resumable_media.requests.download import ChunkedDownload
from google.cloud.storage.resumable_media.requests.download import Download
from google.cloud.storage.resumable_media.requests.upload import MultipartUpload
from google.cloud.storage.resumable_media.requests.download import RawChunkedDownload
from google.cloud.storage.resumable_media.requests.download import RawDownload
from google.cloud.storage.resumable_media.requests.upload import ResumableUpload
from google.cloud.storage.resumable_media.requests.upload import SimpleUpload


__all__ = [
    "ChunkedDownload",
    "Download",
    "MultipartUpload",
    "RawChunkedDownload",
    "RawDownload",
    "ResumableUpload",
    "SimpleUpload",
]
