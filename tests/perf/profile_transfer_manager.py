# Copyright 2023 Google LLC
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

"""Transfer Manager profiling script. This is not an officially supported Google product."""

import logging
import time

from google.cloud.storage import transfer_manager

import benchmarking as bm
import _perf_utils as _pu


def profile_upload_many(args):
    """Profiles a test where multiple objects are uploaded in parallel to a bucket."""
    # Generate random directory and retrieve all file paths
    directory_info = _pu.generate_random_directory(args.num_samples, args.min_size, args.max_size, _pu.DEFAULT_BASE_DIR)
    file_paths = directory_info["paths"]
    bucket = _pu.get_bucket_instance(args.b)
    num_threads = args.t

    start_time = time.monotonic_ns()
    transfer_manager.upload_many_from_filenames(
        bucket,
        file_paths,
        threads=num_threads,
    )
    end_time = time.monotonic_ns()

    elapsed_time = round(
        (end_time - start_time) / 1000
    )  # convert nanoseconds to microseconds

    # Clean up local files and generate results
    _pu.cleanup_directory_tree(_pu.DEFAULT_BASE_DIR)
    res = {
        "ApiName": _pu.DEFAULT_API,
        "RunID": _pu.TIMESTAMP,
        "CpuTimeUs": _pu.NOT_SUPPORTED,
        "AppBufferSize": _pu.NOT_SUPPORTED,
        "LibBufferSize": _pu.DEFAULT_LIB_BUFFER_SIZE,
        "Op": "TM_WRITE",
        "ElapsedTimeUs": elapsed_time,
        "ObjectSize": directory_info["total_size_in_bytes"],
        "Status": ["OK"],
    }
    checksum = None
    res["Crc32cEnabled"] = checksum == "crc32c"
    res["MD5Enabled"] = checksum == "md5"

    return res



def profile_download_many(args):
    """Profiles a test where multiple objects are downloaded in parallel from a bucket."""
    # Generate random directory and retrieve all blob names
    directory_info = _pu.generate_random_directory(args.num_samples, args.min_size, args.max_size, _pu.DEFAULT_BASE_DIR)
    file_paths = directory_info["paths"]
    bucket = _pu.get_bucket_instance(args.b)
    num_threads = args.t
    transfer_manager.upload_many_from_filenames(
        bucket,
        file_paths,
        threads=num_threads,
    )
    blob_names = [blob.name for blob in bucket.list_blobs()]

    start_time = time.monotonic_ns()
    transfer_manager.download_many_to_path(
        bucket,
        blob_names,
        threads=2,
    )
    end_time = time.monotonic_ns()

    elapsed_time = round(
        (end_time - start_time) / 1000
    )  # convert nanoseconds to microseconds

    # Clean up local files and generate results
    _pu.cleanup_directory_tree(_pu.DEFAULT_BASE_DIR)
    res = {
        "ApiName": _pu.DEFAULT_API,
        "RunID": _pu.TIMESTAMP,
        "CpuTimeUs": _pu.NOT_SUPPORTED,
        "AppBufferSize": _pu.NOT_SUPPORTED,
        "LibBufferSize": _pu.DEFAULT_LIB_BUFFER_SIZE,
        "Op": "TM_READ",
        "ElapsedTimeUs": elapsed_time,
        "ObjectSize": directory_info["total_size_in_bytes"],
        "Status": ["OK"],
    }
    checksum = None
    res["Crc32cEnabled"] = checksum == "crc32c"
    res["MD5Enabled"] = checksum == "md5"

    return res


def run_profile_upload_many(args):
    """This is a wrapper used with the main benchmarking framework."""
    results = []
    try:
        res = profile_upload_many(args)
    except Exception as e:
        logging.exception(
            f"Caught an exception while running operation profile_upload_many\n {e}"
        )
        res["Status"] = ["FAIL"]
    else:
        res["Status"] = ["OK"]

    # res = _pu.results_to_csv(res)
    results.append(res)
    return results


def run_profile_download_many(args):
    """This is a wrapper used with the main benchmarking framework."""
    results = []
    try:
        res = profile_download_many(args)
    except Exception as e:
        logging.exception(
            f"Caught an exception while running operation profile_download_many\n {e}"
        )
        res["Status"] = ["FAIL"]
    else:
        res["Status"] = ["OK"]

    # res = _pu.results_to_csv(res)
    results.append(res)
    return results
