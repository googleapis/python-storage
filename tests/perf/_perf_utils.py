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

"""Performance benchmarking helper methods. This is not an officially supported Google product."""

import logging
import os
import random
import shutil
import time
import uuid

from google.cloud import storage

##### DEFAULTS & CONSTANTS #####
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
]
CHECKSUM = ["md5", "crc32c", None]
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")
DEFAULT_API = "JSON"
DEFAULT_BUCKET_LOCATION = "US"
DEFAULT_MIN_SIZE = 4  # 5 KiB
DEFAULT_MAX_SIZE = 5120  # 2 GiB
DEFAULT_NUM_SAMPLES = 10
DEFAULT_NUM_PROCESSES = 16
DEFAULT_NUM_THREADS = 1
DEFAULT_LIB_BUFFER_SIZE = 104857600  # https://github.com/googleapis/python-storage/blob/main/google/cloud/storage/blob.py#L135
NOT_SUPPORTED = -1
DEFAULT_BASE_DIR = "tm-perf-metrics"
DEFAULT_CREATE_SUBDIR_PROBABILITY = 0.1


##### UTILITY METHODS #####

def weighted_random_boolean(create_subdir_probability):
    return random.uniform(0.0, 1.0) <= create_subdir_probability

def generate_random_file(file_name, file_path, size):
    with open(os.path.join(file_path, file_name), "wb") as file_obj:
        file_obj.write(os.urandom(size))

# Creates a random directory structure consisting of subdirectories and random files.
# Returns an array of all the generated paths and total size in bytes of all generated files.
def generate_random_directory(max_objects, min_file_size, max_file_size, base_dir, create_subdir_probability=DEFAULT_CREATE_SUBDIR_PROBABILITY):
    directory_info = {
        "paths": [],
        "total_size_in_bytes": 0,
    }

    file_path = base_dir
    os.makedirs(file_path, exist_ok=True)
    for i in range(max_objects):
        if weighted_random_boolean(create_subdir_probability):
            file_path = f"{file_path}/{uuid.uuid4().hex}"
            os.makedirs(file_path, exist_ok=True)
            directory_info["paths"].append(file_path)
        else:
            file_name = uuid.uuid4().hex
            rand_size = random.randrange(min_file_size, max_file_size)
            generate_random_file(file_name, file_path, rand_size)
            directory_info["total_size_in_bytes"] += rand_size
            directory_info["paths"].append(os.path.join(file_path, file_name))     
    
    return directory_info

def results_to_csv(res):
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
    ]

def log_performance(func, elapsed_time, checksum=None, api=DEFAULT_API, lib_buffer_size=DEFAULT_LIB_BUFFER_SIZE, cputime=NOT_SUPPORTED, app_buffer_size=NOT_SUPPORTED):
    """Log latency and throughput output per operation call."""
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

    checksum = None
    num = None
    res["ElapsedTimeUs"] = elapsed_time
    res["ObjectSize"] = 16
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
    ]

def cleanup_directory_tree(directory):
    """Clean up directory tree on disk."""
    try:
        shutil.rmtree(directory)
    except Exception as e:
        logging.exception(f"Caught an exception while deleting local directory\n {e}")
    print("Successfully removed local directory")

def cleanup_file(file_path):
    """Clean up local file on disk."""
    try:
        os.remove(file_path)
    except Exception as e:
        logging.exception(f"Caught an exception while deleting local file\n {e}")

def get_bucket_instance(bucket_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        client.create_bucket(bucket)
    return bucket