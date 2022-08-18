# Copyright 2022 Google LLC
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

from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket

import concurrent.futures

import tempfile


def upload_many(
    file_blob_pairs,
    skip_if_exists=False,
    upload_kwargs=None,
    max_workers=None,
    deadline=None,
    raise_exception=False
):
    if upload_kwargs is None:
        upload_kwargs = {}
    if skip_if_exists:
        upload_kwargs["if_not_generation_match"] = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for path_or_file, blob in file_blob_pairs:
            method = blob.upload_from_filename if isinstance(path_or_file, str) else blob.upload_from_file
            futures.append(executor.submit(method, path_or_file, **upload_kwargs))
    results = []
    concurrent.futures.wait(
        futures,
        timeout=deadline,
        return_when=concurrent.futures.ALL_COMPLETED)
    for future in futures:
        if not raise_exception:
            exp = future.exception()
            if exp:
                results.append(exp)
                continue
        results.append(future.result())
    return results


def download_many(
    blob_file_pairs,
    download_kwargs=None,
    max_workers=None,
    deadline=None,
    raise_exception=False
):
    if download_kwargs is None:
        download_kwargs = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for blob, path_or_file in blob_file_pairs:
            method = blob.download_to_filename if isinstance(path_or_file, str) else blob.download_to_file
            futures.append(executor.submit(method, path_or_file, **download_kwargs))
    results = []
    concurrent.futures.wait(futures, timeout=deadline,
        return_when=concurrent.futures.ALL_COMPLETED)
    for future in futures:
        if not raise_exception:
            exp = future.exception()
            if exp:
                results.append(exp)
                continue
        results.append(future.result())
    return results


def download_chunks_concurrently_to_file(
    blob,
    file_obj,
    chunk_size=200*1024*1024,
    max_workers=None,
    download_kwargs=None,
    deadline=None
):
    # We must know the size of the object, and the generation.
    if not blob.size or not blob.generation:
        blob.reload()

    chunks = math.ceil(chunk_size / blob.size)

    def download_range_via_tempfile(blob, file_obj, start, end, download_kwargs):
        tmp = tempfile.TemporaryFile()
        blob.download_to_file(tmp, start=start, end=end, **download_kwargs)
        return tmp

    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        cursor = 0
        while cursor < blob.size:
            start = cursor
            cursor = min(cursor+chunk_size, blob.size)
            futures.append(
                executor.submit(download_range_via_tempfile, blob, file_obj, start=start, end=cursor-1, download_kwargs=download_kwargs))

    # Wait until all futures are done and process them in order.
    concurrent.futures.wait(timeout=deadline,
        return_when=concurrent.futures.ALL_COMPLETED)
    for future in futures:
        tmp = future.result()
        tmp.seek(0)
        file_obj.write(tmp.read())


def upload_many_from_filenames(
    bucket,
    filenames,
    root,
    prefix="",
    skip_if_exists=False,
    blob_constructor_kwargs=None,
    upload_kwargs=None,
    max_workers=None,
    deadline=None,
    raise_exception=False
):
    file_blob_pairs = []

    for filename in filenames:
        path = root + filename
        blob_name = prefix + filename
        blob = bucket.blob(blob_name, **blob_constructor_kwargs)
        file_blob_pairs.append((path, blob))

    return upload_many(
        file_blob_pairs,
        skip_if_exists=skip_if_exists,
        upload_kwargs=upload_kwargs,
        max_workers=max_workers,
        deadline=deadline,
        raise_exception=False
    )


def download_many_to_path(
    bucket,
    blob_names,
    path_root,
    blob_name_prefix="",
    download_kwargs=None,
    max_workers=None,
    deadline=None,
    raise_exception=False
):
    blob_file_pairs = []

    for blob_name in blob_names:
        full_blob_name = blob_name_prefix + blob_name
        path = path_root + blob_name
        blob_file_pairs.append((bucket.blob(full_blob_name), path))

    return download_many(
        blob_file_pairs,
        download_kwargs=download_kwargs,
        max_workers=max_workers,
        deadline=deadline,
        raise_exception=False
    )
