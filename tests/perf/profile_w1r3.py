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

"""Workload W1R3 profiling script. This is not an officially supported Google product."""

import logging
import os
import random
import time
import uuid

from functools import partial, update_wrapper

from google.cloud import storage

import _perf_utils as _pu


def log_performance(func):
    """Log latency and throughput output per operation call."""
    # Holds benchmarking results for each operation
    res = {
        "ApiName": _pu.DEFAULT_API,
        "RunID": _pu.TIMESTAMP,
        "CpuTimeUs": _pu.NOT_SUPPORTED,
        "AppBufferSize": _pu.NOT_SUPPORTED,
        "LibBufferSize": _pu.DEFAULT_LIB_BUFFER_SIZE,
    }

    try:
        elapsed_time = func()
    except Exception as e:
        logging.exception(
            f"Caught an exception while running operation {func.__name__}\n {e}"
        )
        res["Status"] = ["FAIL"]
        elapsed_time = _pu.NOT_SUPPORTED
    else:
        res["Status"] = ["OK"]

    checksum = func.keywords.get("checksum")
    num = func.keywords.get("num", None)
    res["ElapsedTimeUs"] = elapsed_time
    res["ObjectSize"] = func.keywords.get("size")
    res["Crc32cEnabled"] = checksum == "crc32c"
    res["MD5Enabled"] = checksum == "md5"
    res["Op"] = func.__name__
    if res["Op"] == "READ":
        res["Op"] += f"[{num}]"

    return res


def WRITE(bucket, blob_name, checksum, size, **kwargs):
    """Perform an upload and return latency."""
    blob = bucket.blob(blob_name)
    file_path = f"{os.getcwd()}/{uuid.uuid4().hex}"
    # Create random file locally on disk
    with open(file_path, "wb") as file_obj:
        file_obj.write(os.urandom(size))

    start_time = time.monotonic_ns()
    blob.upload_from_filename(file_path, checksum=checksum, if_generation_match=0)
    end_time = time.monotonic_ns()

    elapsed_time = round(
        (end_time - start_time) / 1000
    )  # convert nanoseconds to microseconds

    # Clean up local file
    cleanup_file(file_path)

    return elapsed_time


def READ(bucket, blob_name, checksum, **kwargs):
    """Perform a download and return latency."""
    blob = bucket.blob(blob_name)
    if not blob.exists():
        raise Exception("Blob does not exist. Previous WRITE failed.")

    file_path = f"{os.getcwd()}/{blob_name}"
    with open(file_path, "wb") as file_obj:
        start_time = time.monotonic_ns()
        blob.download_to_file(file_obj, checksum=checksum)
        end_time = time.monotonic_ns()

    elapsed_time = round(
        (end_time - start_time) / 1000
    )  # convert nanoseconds to microseconds

    # Clean up local file
    cleanup_file(file_path)

    return elapsed_time


def cleanup_file(file_path):
    """Clean up local file on disk."""
    try:
        os.remove(file_path)
    except Exception as e:
        logging.exception(f"Caught an exception while deleting local file\n {e}")


def _wrapped_partial(func, *args, **kwargs):
    """Helper method to create partial and propagate function name and doc from original function."""
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func


def _generate_func_list(bucket_name, min_size, max_size):
    """Generate Write-1-Read-3 workload."""
    # generate randmon size in bytes using a uniform distribution
    size = random.randrange(min_size, max_size)
    blob_name = f"{_pu.TIMESTAMP}-{uuid.uuid4().hex}"

    # generate random checksumming type: md5, crc32c or None
    idx_checksum = random.choice([0, 1, 2])
    checksum = _pu.CHECKSUM[idx_checksum]

    func_list = [
        _wrapped_partial(
            WRITE,
            storage.Client().bucket(bucket_name),
            blob_name,
            size=size,
            checksum=checksum,
        ),
        *[
            _wrapped_partial(
                READ,
                storage.Client().bucket(bucket_name),
                blob_name,
                size=size,
                checksum=checksum,
                num=i,
            )
            for i in range(3)
        ],
    ]
    return func_list


def benchmark_runner(args):
    """Run benchmarking iterations."""
    results = []
    for func in _generate_func_list(args.b, args.min_size, args.max_size):
        results.append(log_performance(func))

    return results
