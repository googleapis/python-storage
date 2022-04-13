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

"""Performance benchmarking script. This is not an officially supported Google product."""

import argparse
import csv
import logging
import multiprocessing
import os
import random
import tempfile
import time
import uuid

from functools import partial, update_wrapper

from google.cloud import storage


##### DEFAULTS, CONSTANTS & CLI PARAMETERS #####
HEADER = [
    "Op",
    "ObjectSize",
    "AppBufferSize",
    "LibBufferSize",
    "Crc32cEnabled",
    "MD5Enabled",
    "ApiName",
    "ElapsedTimeUs",
    "CpuTimeUs",
    "Status",
    "RunID",
]
CHECKSUM = ["md5", "crc32c"]
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")
DEFAULT_API = "JSON"
DEFAULT_BUCKET_LOCATION = "US"
DEFAULT_MIN_SIZE = 5120
DEFAULT_MAX_SIZE = 16384
DEFAULT_NUM_SAMPLES = 1000
DEFAULT_NUM_PROCESSES = 10
DEFAULT_LIB_BUFFER_SIZE = 104857600
NOT_SUPPORTED = -1

parser = argparse.ArgumentParser()
parser.add_argument(
    "--min_size",
    type=int,
    default=DEFAULT_MIN_SIZE,
    help="Minimum object size in bytes",
)
parser.add_argument(
    "--max_size",
    type=int,
    default=DEFAULT_MAX_SIZE,
    help="Maximum object size in bytes",
)
parser.add_argument(
    "--num_samples", type=int, default=DEFAULT_NUM_SAMPLES, help="Number of iterations"
)
parser.add_argument(
    "--p",
    type=int,
    default=DEFAULT_NUM_PROCESSES,
    help="Number of processes- multiprocessing enabled",
)
parser.add_argument(
    "--r", type=str, default=DEFAULT_BUCKET_LOCATION, help="Bucket location"
)
parser.add_argument(
    "--o",
    type=str,
    default=f"benchmarking{TIMESTAMP}.csv",
    help="File to output results to",
)
args = parser.parse_args()

NUM_SAMPLES = args.num_samples
NUM_PROCESSES = args.p
MIN_SIZE = args.min_size
MAX_SIZE = args.max_size
BUCKET_LOCATION = args.r
CSV_PATH = args.o


def measure_performance(func):
    """Measure latency and throughput per operation call."""
    # Holds benchmarking results for each operation
    res = {
        "ApiName": DEFAULT_API,
        "RunID": TIMESTAMP,
        "CpuTimeUs": NOT_SUPPORTED,
        "AppBufferSize": NOT_SUPPORTED,
        "LibBufferSize": DEFAULT_LIB_BUFFER_SIZE,
    }

    try:
        elapsed_time = func()
    except Exception as e:
        logging.exception(
            f"Caught an exception while running operation {func.__name__}\n {e}"
        )
        res["Status"] = ["FAIL"]
        elapsed_time = NOT_SUPPORTED
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

    return [
        res["Op"],
        res["ObjectSize"],
        res["AppBufferSize"],
        res["LibBufferSize"],
        res["Crc32cEnabled"],
        res["MD5Enabled"],
        res["ApiName"],
        res["ElapsedTimeUs"],
        res["CpuTimeUs"],
        res["Status"],
        res["RunID"],
    ]


def WRITE(bucket, blob_name, checksum, size, **kwargs):
    """Perform an upload and return latency."""
    blob = bucket.blob(blob_name)
    # TemporaryFile is cleaned up upon closing
    with tempfile.NamedTemporaryFile() as f:
        f.write(os.urandom(size))

        start_time = time.monotonic_ns()
        blob.upload_from_filename(f.name, checksum=checksum, if_generation_match=0)
        end_time = time.monotonic_ns()

    elapsed_time = round(
        (end_time - start_time) / 1000
    )  # convert nanoseconds to microseconds
    return elapsed_time


def READ(bucket, blob_name, checksum, **kwargs):
    """Perform a download and return latency."""
    blob = bucket.blob(blob_name)

    start_time = time.monotonic_ns()
    blob.download_as_bytes(checksum=checksum)
    end_time = time.monotonic_ns()

    elapsed_time = round(
        (end_time - start_time) / 1000
    )  # convert nanoseconds to microseconds
    return elapsed_time


def wrapped_partial(func, *args, **kwargs):
    """Helper method to create partial and propagate function name and doc from original function."""
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func


def generate_func_list(bucket_name, min_size, max_size):
    """Generate Write-1-Read-3 workload."""
    # generate randmon size using a uniform distribution
    size = random.randrange(min_size, max_size)
    blob_name = f"{TIMESTAMP}-{uuid.uuid4().hex}"

    # generate random checksumming type using a uniform dist
    idx_checksum = random.randrange(0, 2)
    checksum = CHECKSUM[idx_checksum]

    func_list = [
        wrapped_partial(
            WRITE,
            storage.Client().bucket(bucket_name),
            blob_name,
            size=size,
            checksum=checksum,
        ),
        *[
            wrapped_partial(
                READ,
                storage.Client().bucket(bucket_name),
                blob_name,
                size=size,
                num=i,
                checksum=checksum,
            )
            for i in range(3)
        ],
    ]
    return func_list


def benchmark_runner(x):
    """Run benchmarking iterations."""
    # Create a bucket to run benchmarking
    client = storage.Client()
    bucket_name = uuid.uuid4().hex
    bucket = client.create_bucket(bucket_name, location=BUCKET_LOCATION)

    # Run benchmarking
    results = []
    for i in range(NUM_SAMPLES):
        for func in generate_func_list(bucket_name, MIN_SIZE, MAX_SIZE):
            results.append(measure_performance(func))

    # Cleanup and delete bucket
    try:
        bucket.delete(force=True)
    except Exception as e:
        logging.exception(f"Caught an exception while running retry instructions\n {e}")

    return results


if __name__ == "__main__":
    p = multiprocessing.Pool(NUM_PROCESSES)
    pool_output = p.map(benchmark_runner, range(1))
    with open(CSV_PATH, "w") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        for result in pool_output:
            for row in result:
                writer.writerow(row)
    print(f"Succesfully ran benchmarking. Please find your output log at {CSV_PATH}")
