# Copyright 2026 Google LLC
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
import pytest
import os
import multiprocessing
import logging
from google.cloud import storage

_OBJECT_NAME_PREFIX = "time_based_tests"


# def _upload_worker(args):
#     bucket_name, object_name, object_size = args
#     storage_client = storage.Client()
#     bucket = storage_client.bucket(bucket_name)
#     blob = bucket.blob(object_name)

#     try:
#         blob.reload()
#         if blob.size >= object_size:
#             logging.info(f"Object {object_name} already exists and has the required size.")
#             return object_name, object_size
#     except Exception:
#         pass

#     logging.info(f"Creating object {object_name} of size {object_size} bytes.")
#     # For large objects, it's better to upload in chunks.
#     # Using urandom is slow, so for large objects, we will write the same chunk over and over.
#     chunk_size = 100 * 1024 * 1024  # 100 MiB
#     data_chunk = os.urandom(chunk_size)
#     num_chunks = object_size // chunk_size
#     remaining_bytes = object_size % chunk_size

#     from io import BytesIO
#     with BytesIO() as f:
#         for _ in range(num_chunks):
#             f.write(data_chunk)
#         if remaining_bytes > 0:
#             f.write(data_chunk[:remaining_bytes])
        
#         f.seek(0)
#         blob.upload_from_file(f, size=object_size)

#     logging.info(f"Finished creating object {object_name}.")
#     return object_name, object_size


# def _create_files(num_files, bucket_name, object_size):
#     """
#     Create/Upload objects for benchmarking and return a list of their names.
#     """
#     object_names = [f"{_OBJECT_NAME_PREFIX}_{i}" for i in range(num_files)]

#     args_list = [
#         (bucket_name, object_names[i], object_size) for i in range(num_files)
#     ]

#     # Don't use a pool to avoid contention writing the same objects.
#     # The check for existence should make this fast on subsequent runs.
#     results = [_upload_worker(arg) for arg in args_list]

#     return [r[0] for r in results]


@pytest.fixture
def workload_params(request):
    params = request.param
    files_names = [f'fio-go_storage_fio.0.{i}' for i in range(0, params.num_processes)]
    # files_names = _create_files(
    #     params.num_processes, # One file per process
    #     params.bucket_name,
    #     params.file_size_bytes,
    # )
    return params, files_names
