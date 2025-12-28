from typing import Any


def publish_benchmark_extra_info(
    benchmark: Any, params: Any, benchmark_group: str = "read"
) -> None:
    """
    Helper function to publish benchmark parameters to the extra_info property.
    """
    benchmark.extra_info["num_files"] = params.num_files
    benchmark.extra_info["file_size"] = params.file_size_bytes
    benchmark.extra_info["chunk_size"] = params.chunk_size_bytes
    benchmark.extra_info["pattern"] = params.pattern
    benchmark.extra_info["coros"] = params.num_coros
    benchmark.extra_info["rounds"] = params.rounds
    benchmark.extra_info["bucket_name"] = params.bucket_name
    benchmark.extra_info["bucket_type"] = params.bucket_type
    benchmark.extra_info["processes"] = params.num_processes
    benchmark.group = benchmark_group
