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

import csv
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
DEFAULT_MIN_SIZE = 5120  # 5 KiB
DEFAULT_MAX_SIZE = 2147483648  # 2 GiB
DEFAULT_NUM_SAMPLES = 1000
DEFAULT_NUM_PROCESSES = 1
DEFAULT_NUM_THREADS = 1
DEFAULT_LIB_BUFFER_SIZE = 104857600  # https://github.com/googleapis/python-storage/blob/main/google/cloud/storage/blob.py#L135
NOT_SUPPORTED = -1
DEFAULT_BASE_DIR = "tm-perf-metrics"
DEFAULT_CREATE_SUBDIR_PROBABILITY = 0.1
SSB_SIZE_THRESHOLD_BYTES = 1048576


##### UTILITY METHODS #####


# Returns a boolean value with the provided probability.
def weighted_random_boolean(create_subdir_probability):
    return random.uniform(0.0, 1.0) <= create_subdir_probability


# Creates a random file with the given file name, path and size.
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
        res.get("Op", None),
        res.get("ObjectSize", None),
        res.get("AppBufferSize", None),
        res.get("LibBufferSize", None),
        res.get("Crc32cEnabled", None),
        res.get("MD5Enabled", None),
        res.get("ApiName", None),
        res.get("ElapsedTimeUs", None),
        res.get("CpuTimeUs", None),
        res.get("Status", None),
    ]


def convert_to_csv(filename, results):
    with open(filename, "w") as file:
            writer = csv.writer(file)
            writer.writerow(HEADER)
            # Benchmarking main script uses Multiprocessing Pool.map(),
            # thus results is structured as List[List[Dict[str, any]]].
            for result in results:
                for row in result:
                    writer.writerow(results_to_csv(row))


def convert_to_cloud_monitoring(bucket_name, results):
    # Benchmarking main script uses Multiprocessing Pool.map(),
    # thus results is structured as List[List[Dict[str, any]]].
    for result in results:
        for res in result:
            # Handle failed runs
            if res.get("Status") != ["OK"]:
                # do something such as log error
                continue

            # Log successful benchmark results, aka res["Status"] == ["OK"]
            # If the object size is greater than the defined threshold, report in MiB/s, otherwise report in KiB/s.
            object_size = res.get("ObjectSize")
            elapsed_time_us = res.get("ElapsedTimeUs")
            if object_size >= SSB_SIZE_THRESHOLD_BYTES:
                throughput = object_size / 1024 / 1024 / (elapsed_time_us / 1_000_000)
            else:
                throughput = object_size / 1024 / (elapsed_time_us / 1_000_000)

            cloud_monitoring_output = (
                "throughput{"+
                "timestamp='{}',".format(TIMESTAMP)+
                "library='python-storage',"+
                "api='{}',".format(res.get("ApiName"))+
                "op='{}',".format(res.get("Op"))+
                "object_size='{}',".format(res.get("ObjectSize"))+
                "transfer_offset='0',"+
                "transfer_size='{}',".format(res.get("ObjectSize"))+
                "app_buffer_size='{}',".format(res.get("AppBufferSize"))+
                "crc32c_enabled='{}',".format(res.get("Crc32cEnabled"))+
                "md5_enabled='{}',".format(res.get("MD5Enabled"))+
                "elapsed_time_us='{}',".format(res.get("ElapsedTimeUs"))+
                "cpu_time_us='{}',".format(res.get("CpuTimeUs"))+
                "elapsedmicroseconds='{}',".format(res.get("ElapsedTimeUs"))+
                "peer='',"+
                f"bucket_name='{bucket_name}',"+
                "object_name='',"+
                "generation='',"+
                "upload_id='',"+
                "retry_count='',"+
                "status_code=''}"
                f"{throughput}"
            )
            print(cloud_monitoring_output)


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