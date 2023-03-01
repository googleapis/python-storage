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

"""Performance benchmarking main script. This is not an officially supported Google product."""

import argparse
import csv
import logging
import multiprocessing


from google.cloud import storage
import _perf_utils as _pu
import profile_transfer_manager as tm
import profile_w1r3 as w1r3


##### PROFILE BENCHMARKING TEST TYPES #####
PROFILE_WRITE_ONE_READ_THREE = 'w1r3'
PROFILE_TM_UPLOAD_MANY = "upload_many"
PROFILE_TM_DOWNLOAD_MANY = "download_many"


def main(args):
    print(f"Start benchmarking main script")
    # Create a storage bucket to run benchmarking
    client = storage.Client()
    if not client.bucket(args.b).exists():
        bucket = client.create_bucket(args.b, location=args.r)

    # Define test type and number of processes to run benchmarking.
    # Note that transfer manager tests defaults to using 1 process.
    num_processes = 1
    test_type = args.test_type
    if test_type == PROFILE_TM_UPLOAD_MANY:
        benchmark_runner = tm.run_profile_upload_many
        print(f"Running {test_type} benchmarking with {args.t} threads.")
        print(f"Note that Transfer Manager benchmarking defaults to using {num_processes} process.")
    elif test_type == PROFILE_TM_DOWNLOAD_MANY:
        benchmark_runner = tm.run_profile_download_many
        print(f"Running {test_type} benchmarking with {args.t} threads.")
        print(f"Note that Transfer Manager benchmarking defaults to using {num_processes} process.")
    elif test_type == PROFILE_WRITE_ONE_READ_THREE:
        num_processes = args.p
        benchmark_runner = w1r3.benchmark_runner
        print(f"A total of {num_processes} processes are created to run benchmarking {test_type}")

    p = multiprocessing.Pool(num_processes)
    pool_output = p.map(benchmark_runner, [args for _ in range(args.num_samples)])

    output_type = args.output_type
    # Output to Cloud Monitoring
    if output_type == "cloud-monitoring":
        SB_SIZE_THRESHOLD_BYTES = 1048576
        bucketName = args.b
        for result in pool_output:
            for res in result:
                # Handle failed runs
                if res.get("Status") != ["OK"]:
                    # do something such as log error
                    continue

                # Log successful benchmark results, aka res["Status"] == ["OK"]
                # If the object size is greater than the defined threshold, report in MiB/s, otherwise report in KiB/s.
                object_size = res.get("ObjectSize")
                elapsed_time_us = res.get("ElapsedTimeUs")
                if object_size >= SB_SIZE_THRESHOLD_BYTES:
                    throughput = object_size / 1024 / 1024 / (elapsed_time_us / 1_000_000)
                else:
                    throughput = object_size / 1024 / (elapsed_time_us / 1_000_000)

                cloud_monitoring_output = (
                    "throughput{"+
                    "timestamp='{}',".format(_pu.TIMESTAMP)+
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
                    f"bucket_name='{bucketName}',"+
                    "object_name='',"+
                    "generation='',"+
                    "upload_id='',"+
                    "retry_count='',"+
                    "status_code=''}"
                    f"{throughput}"
                )
                print(cloud_monitoring_output)
    elif output_type == "csv":
        # Output to CSV file
        with open(args.o, "w") as file:
            writer = csv.writer(file)
            writer.writerow(_pu.HEADER)
            for result in pool_output:
                for row in result:
                    writer.writerow(_pu.results_to_csv(row))
        print(f"Succesfully ran benchmarking. Please find your output log at {args.o}")


    # Cleanup and delete bucket
    try:
        bucket.delete(force=True)
    except Exception as e:
        logging.exception(f"Caught an exception while deleting bucket\n {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test_type",
        type=str,
        default=PROFILE_TM_UPLOAD_MANY,
        help="Benchmarking test type",
    )
    parser.add_argument(
        "--min_size",
        type=int,
        default=_pu.DEFAULT_MIN_SIZE,
        help="Minimum object size in bytes",
    )
    parser.add_argument(
        "--max_size",
        type=int,
        default=_pu.DEFAULT_MAX_SIZE,
        help="Maximum object size in bytes",
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=_pu.DEFAULT_NUM_SAMPLES,
        help="Number of iterations",
    )
    parser.add_argument(
        "--p",
        type=int,
        default=_pu.DEFAULT_NUM_PROCESSES,
        help="Number of processes- multiprocessing enabled",
    )
    parser.add_argument(
        "--t",
        type=int,
        default=_pu.DEFAULT_NUM_THREADS,
        help="Number of threads",
    )
    parser.add_argument(
        "--b",
        type=str,
        default=f"benchmarking{_pu.TIMESTAMP}",
        help="Storage bucket name",
    )
    parser.add_argument(
        "--r", type=str, default=_pu.DEFAULT_BUCKET_LOCATION, help="Bucket location"
    )
    parser.add_argument(
        "--output_type",
        type=str,
        default="csv",
        help="Ouput format, csv or cloud-monitoring",
    )
    parser.add_argument(
        "--o",
        type=str,
        default=f"output_benchmarks{_pu.TIMESTAMP}.csv",
        help="File to output results to",
    )
    parser.add_argument(
        "--tmp_dir",
        type=str,
        default=_pu.DEFAULT_BASE_DIR ,
        help="Storage bucket name",
    )
    args = parser.parse_args()

    main(args)
