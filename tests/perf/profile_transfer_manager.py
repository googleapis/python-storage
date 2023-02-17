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

import csv
import logging
import time

from google.cloud import storage
from google.cloud.storage import transfer_manager
from . import _perf_utils as _pu


### PERFORMANCE PROFILING SETUP ###
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")

client = storage.Client()
if not client.bucket(TIMESTAMP).exists():
    BUCKET = client.create_bucket(TIMESTAMP)


# Profiles a test where multiple objects are uploaded in parallel to a bucket.
def profile_upload_many():
    # Generate random directory and retrieve all file paths
    directory_info = _pu.generate_random_directory(_pu.DEFAULT_NUM_SAMPLES, _pu.DEFAULT_MIN_SIZE, _pu.DEFAULT_MAX_SIZE, _pu.DEFAULT_BASE_DIR)
    file_paths = directory_info["paths"]

    start_time = time.monotonic_ns()
    transfer_manager.upload_many_from_filenames(
        BUCKET,
        file_paths,
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
        "RunID": TIMESTAMP,
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

    return _pu.results_to_csv(res)


# Profiles a test where multiple objects are downloaded in parallel from a bucket.
def profile_download_many():
    # Generate random directory and retrieve all blob names
    directory_info = _pu.generate_random_directory(_pu.DEFAULT_NUM_SAMPLES, _pu.DEFAULT_MIN_SIZE, _pu.DEFAULT_MAX_SIZE, _pu.DEFAULT_BASE_DIR)
    file_paths = directory_info["paths"]
    transfer_manager.upload_many_from_filenames(
        BUCKET,
        file_paths,
        threads=2,
    )
    blob_names = [blob.name for blob in BUCKET.list_blobs()]

    start_time = time.monotonic_ns()
    transfer_manager.download_many_to_path(
        BUCKET,
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
        "RunID": TIMESTAMP,
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

    return _pu.results_to_csv(res)


def main():
    # Entry point to run Transfer Manager profiling
    results = profile_download_many()

    # Output to CSV file
    csv_file = f"tm_profiling_{TIMESTAMP}.csv"
    with open(csv_file, "w") as file:
        writer = csv.writer(file)
        writer.writerow(_pu.HEADER)
        writer.writerow(results)

    print(f"Succesfully ran benchmarking. Please find your output log at {csv_file}")

    # Cleanup and delete bucket
    try:
        BUCKET.delete(force=True)
    except Exception as e:
        logging.exception(f"Caught an exception while deleting bucket\n {e}")

main()