from dataclasses import dataclass

# import os

# # Get the benchmark bucket name from the GCS_BENCHMARK_BUCKET environment
# # variable. If the environment variable is not set, a default name is used.
# _DEFAULT_RAPID_ZONAL_BUCKET = "chandrasiri-rs"
# _DEFAULT_STANDARD_BUCKET = "gcs-pytest-benchmark-standard-bucket"

# # env name should have prefix "GCS_PY_SDK_BENCH_" + default varible name.
# RAPID_ZONAL_BUCKET = os.environ.get("GCS_PY_SDK_BENCH_RAPID_ZONAL_BUCKET", _DEFAULT_RAPID_ZONAL_BUCKET)
# STANDARD_BUCKET = os.environ.get("GCS_PY_SDK_BENCH_STANDARD_BUCKET", _DEFAULT_STANDARD_BUCKET)



@dataclass
class ReadParameters:
    name: str
    workload_name: str
    pattern: str
    bucket_name: str
    bucket_type: str
    num_coros: int
    num_processes: int
    num_files: int
    rounds: int
    chunk_size_bytes: int
    file_size_bytes: int
