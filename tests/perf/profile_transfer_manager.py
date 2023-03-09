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

import _perf_utils as _pu


def profile_upload_many(args):
    """Profile a test where multiple objects are uploaded in parallel to a bucket."""
    # Generate random directory and retrieve all file paths
    directory_info = _pu.generate_random_directory(
        args.samples, args.min_size, args.max_size, args.tmp_dir
    )
    file_paths = directory_info["paths"]
    bucket = _pu.get_bucket_instance(args.bucket)
    num_threads = args.threads

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
    total_size_in_bytes = directory_info["total_size_in_bytes"]
    # Clean up local files and generate results
    _pu.cleanup_directory_tree(_pu.DEFAULT_BASE_DIR)

    return elapsed_time, total_size_in_bytes


def profile_download_many(args):
    """Profile a test where multiple objects are downloaded in parallel from a bucket."""
    # Generate random directory and retrieve all blob names
    directory_info = _pu.generate_random_directory(
        args.samples, args.min_size, args.max_size, args.tmp_dir
    )
    file_paths = directory_info["paths"]
    bucket = _pu.get_bucket_instance(args.bucket)
    num_threads = args.threads
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
    total_size_in_bytes = directory_info["total_size_in_bytes"]

    # Clean up local files and generate results
    _pu.cleanup_directory_tree(_pu.DEFAULT_BASE_DIR)

    return elapsed_time, total_size_in_bytes


def log_performance(args, elapsed_time, status, failure_msg, op, size, checksum=None):
    """Hold benchmarking results per operation call."""
    res = {
        "Op": op,
        "ElapsedTimeUs": elapsed_time,
        "ApiName": args.api,
        "RunID": _pu.TIMESTAMP,
        "CpuTimeUs": _pu.NOT_SUPPORTED,
        "AppBufferSize": _pu.NOT_SUPPORTED,
        "LibBufferSize": _pu.DEFAULT_LIB_BUFFER_SIZE,
        "ChunkSize": 0,
        "ObjectSize": size,
        "TransferSize": size,
        "TransferOffset": 0,
        "RangeReadSize": args.range_read_size,
        "BucketName": args.bucket,
        "Library": "python-storage",
        "Crc32cEnabled": checksum == "crc32c",
        "MD5Enabled": checksum == "md5",
        "FailureMsg": failure_msg,
        "Status": status,
    }

    return res


def run_profile_upload_many(args):
    """Run upload many benchmarking. This is a wrapper used with the main benchmarking framework."""
    results = []
    op = "UPLOAD_MANY"
    failure_msg = ""
    try:
        elapsed_time, size = profile_upload_many(args)
    except Exception as e:
        failure_msg = f"Caught an exception while running operation {op}\n {e}"
        logging.exception(failure_msg)
        status = ["FAIL"]
        elapsed_time = _pu.NOT_SUPPORTED
        size = 0
    else:
        status = ["OK"]

    # Benchmarking main script uses Multiprocessing Pool.map(),
    # thus we structure results as List[List[Dict[str, any]]].
    res = log_performance(args, elapsed_time, status, failure_msg, op, size)
    results.append(res)
    return results


def run_profile_download_many(args):
    """Run download many benchmarking. This is a wrapper used with the main benchmarking framework."""
    results = []
    op = "DOWNLOAD_MANY"
    failure_msg = ""
    try:
        elapsed_time, size = profile_download_many(args)
    except Exception as e:
        failure_msg = f"Caught an exception while running operation {op}\n {e}"
        logging.exception(failure_msg)
        status = ["FAIL"]
        elapsed_time = _pu.NOT_SUPPORTED
        size = 0
    else:
        status = ["OK"]

    # Benchmarking main script uses Multiprocessing Pool.map(),
    # thus we structure results as List[List[Dict[str, any]]].
    res = log_performance(args, elapsed_time, status, failure_msg, op, size)
    results.append(res)
    return results
