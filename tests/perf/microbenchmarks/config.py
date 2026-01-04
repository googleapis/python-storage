# nit: TODO: rename it to config_to_params.py
import itertools
import os
from typing import Dict, List

import yaml

try:
    from tests.perf.microbenchmarks.parameters import ReadParameters, WriteParameters
except ModuleNotFoundError:
    from parameters import ReadParameters, WriteParameters





def _get_params() -> Dict[str, List[ReadParameters]]:
    """
    Docstring for _get_params
    1. this function output a list of readParameters.
    2. to populate the values of readparameters, use default values from config.yaml
    3. generate all possible params , ie
        no. of params should be equal to bucket_type*file_size_mib, chunk_size * process * coros
        you may use itertools.product
    """
    params: Dict[str, List[ReadParameters]] = {}
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    common_params = config["common"]
    bucket_types = common_params["bucket_types"]
    file_sizes_mib = common_params["file_sizes_mib"]
    chunk_sizes_mib = common_params["chunk_sizes_mib"]
    rounds = common_params["rounds"]

    bucket_map = {
        "zonal": config["defaults"]["DEFAULT_RAPID_ZONAL_BUCKET"],
        "regional": config["defaults"]["DEFAULT_STANDARD_BUCKET"],
    }

    for workload in config["workload"]:
        workload_name = workload["name"]
        params[workload_name] = []
        pattern = workload["pattern"]
        processes = workload["processes"]
        coros = workload["coros"]

        # Create a product of all parameter combinations
        product = itertools.product(
            bucket_types,
            file_sizes_mib,
            chunk_sizes_mib,
            processes,
            coros,
        )

        for (
            bucket_type,
            file_size_mib,
            chunk_size_mib,
            num_processes,
            num_coros,
        ) in product:
            file_size_bytes = file_size_mib * 1024 * 1024
            chunk_size_bytes = chunk_size_mib * 1024 * 1024
            bucket_name = bucket_map[bucket_type]

            if "single_file" in workload_name:
                num_files = 1
            else:
                num_files = num_processes * num_coros

            # Create a descriptive name for the parameter set
            name = f"{pattern}_{bucket_type}_{num_processes}p_{num_coros}c"
            # name = f"{workload_name}"

            params[workload_name].append(
                ReadParameters(
                    name=name,
                    workload_name=workload_name,
                    pattern=pattern,
                    bucket_name=bucket_name,
                    bucket_type=bucket_type,
                    num_coros=num_coros,
                    num_processes=num_processes,
                    num_files=num_files,
                    rounds=rounds,
                    chunk_size_bytes=chunk_size_bytes,
                    file_size_bytes=file_size_bytes,
                )
            )
    # print(params)
    return params


def get_write_params() -> Dict[str, List[WriteParameters]]:
    """
    Docstring for get_write_params
    1. this function output a list of WriteParameters.
    2. to populate the values of WriteParameters, use default values from config_writes.yaml
    3. generate all possible params , ie
        no. of params should be equal to bucket_type*file_size_mib, chunk_size * process * coros
        you may use itertools.product
    """
    params: Dict[str, List[WriteParameters]] = {}
    config_path = os.path.join(os.path.dirname(__file__), "config_writes.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    common_params = config["common"]
    bucket_types = common_params["bucket_types"]
    file_sizes_mib = common_params["file_sizes_mib"]
    chunk_sizes_mib = common_params["chunk_sizes_mib"]
    rounds = common_params["rounds"]

    bucket_map = {
        "zonal": config["defaults"]["DEFAULT_RAPID_ZONAL_BUCKET"],
        "regional": config["defaults"]["DEFAULT_STANDARD_BUCKET"],
    }

    for workload in config["workload"]:
        workload_name = workload["name"]
        params[workload_name] = []
        processes = workload["processes"]
        coros = workload["coros"]

        # Create a product of all parameter combinations
        product = itertools.product(
            bucket_types,
            file_sizes_mib,
            chunk_sizes_mib,
            processes,
            coros,
        )

        for (
            bucket_type,
            file_size_mib,
            chunk_size_mib,
            num_processes,
            num_coros,
        ) in product:
            file_size_bytes = file_size_mib * 1024 * 1024
            chunk_size_bytes = chunk_size_mib * 1024 * 1024
            bucket_name = bucket_map[bucket_type]

            if "single_file" in workload_name:
                num_files = 1
            else:
                num_files = num_processes * num_coros

            # Create a descriptive name for the parameter set
            name = f"{workload_name}_{bucket_type}_{num_processes}p_{num_coros}c"

            params[workload_name].append(
                WriteParameters(
                    name=name,
                    workload_name=workload_name,
                    bucket_name=bucket_name,
                    bucket_type=bucket_type,
                    num_coros=num_coros,
                    num_processes=num_processes,
                    num_files=num_files,
                    rounds=rounds,
                    chunk_size_bytes=chunk_size_bytes,
                    file_size_bytes=file_size_bytes,
                )
            )
    return params


if __name__ == "__main__":
    import sys
    # params = _get_params()
    # print("Read params:")
    # print('keys (num_workload in params', len(params), sys.getsizeof(params))
    # if 'read_seq' in params:
    #     print(params['read_seq'], len(params['read_seq']))

    write_params = get_write_params()

    print(write_params)
    print("\nWrite params:")
    print(
        "keys (num_workload in params", len(write_params), sys.getsizeof(write_params)
    )
    # if 'write_seq' in write_params:
    #     print(write_params['write_seq'], len(write_params['write_seq']))
