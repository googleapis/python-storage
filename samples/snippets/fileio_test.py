# Copyright 2021 Google LLC
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

import uuid

import storage_fileio_read_blob
import storage_fileio_write_blob


def test_fileio_write_read(bucket, capsys):
    blob_name = "test-fileio-{}".format(uuid.uuid4())
    storage_fileio_write_blob.write_blob(bucket.name, blob_name)
    out, _ = capsys.readouterr()
    assert f"Wrote csv to storage object {blob_name} in bucket {bucket.name}." in out
    storage_fileio_read_blob.read_blob(bucket.name, blob_name)
    out, _ = capsys.readouterr()
    assert f"Read csv from storage object {blob_name} in bucket {bucket.name}." in out
