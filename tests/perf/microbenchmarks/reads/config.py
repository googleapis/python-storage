# Copyright 2026 Google LLC
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
import itertools
import os
from typing import Dict, List

import yaml

try:
    from tests.perf.microbenchmarks.reads.parameters import ReadParameters
except ModuleNotFoundError:
    from reads.parameters import ReadParameters


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
        "zonal": os.environ.get("DEFAULT_RAPID_ZONAL_BUCKET", config['defaults']['DEFAULT_RAPID_ZONAL_BUCKET']),
        "regional": os.environ.get("DEFAULT_STANDARD_BUCKET", config['defaults']['DEFAULT_STANDARD_BUCKET'])
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
    return params
