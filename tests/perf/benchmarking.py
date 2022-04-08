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
import random
import time
import uuid
 
from functools import partial, update_wrapper

from google.cloud import storage


##### CONSTANTS #####
HEADER = ["Op", "ObjectSize", "AppBufferSize", "LibBufferSize", "Crc32cEnabled", "MD5Enabled", "ApiName", "ElapsedTimeUs", "CpuTimeUs", "Status", "RunID"]
CHECKSUM = ["md5", "crc32c"]
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")

# ##### CLI PARAMETERS & DEFAULTS #####
parser = argparse.ArgumentParser()
parser.add_argument("--min_size", type=int, default=5120, help="Minimum object size in bytes") 
parser.add_argument("--max_size", type=int, default=16384, help="Maximum object size in bytes") 
parser.add_argument("--num_samples", type=int, default=1000, help="Number of iterations") 
parser.add_argument("--p", type=int, default=10, help="Number of processes- multiprocessing enabled") 
parser.add_argument("--r", type=str, default="US", help="Bucket location") 
parser.add_argument("--o", type=str, default=f"benchmarking{TIMESTAMP}.csv", help="File to output results to") 
args = parser.parse_args()

NUM_SAMPLES = args.num_samples
NUM_PROCESSES = args.p
MIN_SIZE = args.min_size
MAX_SIZE = args.max_size
BUCKET_LOCATION= args.r
CSV_PATH = args.o


def measure_performance(func):
    """Measure latency and throughput per operation call."""
    # Holds benchmarking results for each operation
    res = {
        "ApiName": "JSON",
        "RunID": TIMESTAMP,
        "CpuTimeUs": -1,
        "AppBufferSize": 1024,
        "LibBufferSize": 104857600,
        "Status": ["OK"],
    }

    # Measures time for each operation
    start_time = time.monotonic_ns()
    try:
        func()
    except Exception as e:
        res["Status"] = ["FAIL"]
    end_time = time.monotonic_ns()

    res["ElapsedTimeUs"] = round((end_time-start_time) / 1000)   # convert nanoseconds to microseconds
    res["ObjectSize"] = func.keywords.get("size")
    res["Crc32cEnabled"] = func.keywords.get("Crc32cEnabled")
    res["MD5Enabled"] = func.keywords.get("MD5Enabled")
    num = func.keywords.get("num", None)
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
        res["RunID"]
    ] 
 
def WRITE(bucket, blob_name, payload, **kwargs):
    """Perform an upload."""
    checksum = kwargs.get("checksum")
 
    blob = bucket.blob(blob_name)
    blob.upload_from_string(payload, checksum=checksum)
 
def READ(bucket, blob_name, **kwargs):
    """Perform a download."""
    checksum = kwargs.get("checksum")
 
    blob = bucket.blob(blob_name)
    blob.download_as_bytes(checksum=checksum)
 
def _create_block(desired_bytes):
    """Helper method to generate contents by specified size."""
    return "A" * desired_bytes
 
def wrapped_partial(func, *args, **kwargs):
    """Helper method to create partial and propagate function name and doc from original function."""
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func
 
def generate_func_list(bucket_name, min_size, max_size):
    """Generate Write-1-Read-3 workload."""
    blob_name = uuid.uuid4().hex
    # generate randmon size payload using a uniform dist
    size = random.randrange(min_size, max_size)
    payload = _create_block(size)
 
    # generate random checksumming type using a uniform dist
    idx_checksum = random.randrange(0, 2)
    md5_enabled = idx_checksum == 0
    crc32c_enabled = not md5_enabled
    checksum = CHECKSUM[idx_checksum]
 
    func_list = [
                    wrapped_partial(WRITE, storage.Client().bucket(bucket_name), blob_name, payload, size=size, Crc32cEnabled=crc32c_enabled, MD5Enabled=md5_enabled, checksum=checksum), 
                    *[wrapped_partial(READ, storage.Client().bucket(bucket_name), blob_name, size=size, num=i, Crc32cEnabled=crc32c_enabled, MD5Enabled=md5_enabled, checksum=checksum) for i in range(3)]
                ]
    return func_list
 
def main_profiling(x):
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
    pool_output = p.map(main_profiling, range(1))
    with open(CSV_PATH, 'w') as file:
      writer = csv.writer(file)
      writer.writerow(HEADER)
      for result in pool_output:
        for row in result:
          writer.writerow(row)
    print(f"Succesfully ran benchmarking. Please find your output log at {CSV_PATH}")