from dataclasses import dataclass


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


@dataclass
class WriteParameters:
    name: str
    workload_name: str
    bucket_name: str
    bucket_type: str
    num_coros: int
    num_processes: int
    num_files: int
    rounds: int
    chunk_size_bytes: int
    file_size_bytes: int