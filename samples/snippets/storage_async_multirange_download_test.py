# Copyright 2024 Google LLC
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

import os
import pytest
from google.cloud import storage
from google.cloud.storage import transfer_manager

from samples.snippets import storage_async_multirange_download


@pytest.mark.asyncio
async def test_async_multirange_download(bucket: storage.Bucket, blob: storage.Blob, tmpdir: str):
    # Upload a test file
    content = b"This is a test file.\nIt has multiple lines.\nAnd some ranges we can download."
    blob.upload_from_string(content)

    # Create a temporary file for the download
    destination_file = os.path.join(tmpdir, "destination.txt")

    # Download the file in multiple ranges
    await storage_async_multirange_download.async_multirange_download(
        bucket_name=bucket.name, blob_name=blob.name, destination_file_name=destination_file
    )

    # Verify that the file was downloaded correctly
    with open(destination_file, "rb") as f:
        downloaded_content = f.read()
    expected_content = content[:100] + content[100:200] + content[200:300]
    assert downloaded_content == expected_content
