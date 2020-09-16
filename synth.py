# Copyright 2020 Google LLC
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

"""This script is used to synthesize generated parts of this library."""

from io import UnsupportedOperation
from os import uname
import re

import synthtool as s
from synthtool import gcp

gapic = gcp.GAPICBazel()
common = gcp.CommonTemplates()
versions = ["v1"]

# ----------------------------------------------------------------------------
# Generate asset GAPIC layer
# ----------------------------------------------------------------------------
for version in versions:
    library = gapic.py_library(
        service="storage",
        version=version,
        bazel_target=f"//google/storage/{version}:storage-{version}-py",
    )
    excludes = [google/cloud/storage.py"]
    s.move(library / f"storage-{version}-py/", ".")#, excludes=excludes)

    # TODO: metadata is an arg used by top-level gapic. Modify method
    # signatures accordingly.
    # s.replace(
    #     f"google/cloud/storage_{version}/storage_client.py",
    #     "(),\n.*)metadata=None,(\n.*[a-z])", 
    #     "$1api_metadata=None,$2"
    # )

    # Fix bad docstrings
    s.replace(
        f"google/cloud/storage_{version}/storage_client.py",
        "``\\",
        "``"
    )

    # Remove unused imports
    unused_imports = [
        "import grpc",
        "from google.cloud.storage_v1 import enums",
        "from google.cloud.storage_v1.proto import storage_pb2_grpc",
        "from google.cloud.storage_v1.proto import storage_resources_pb2",
        "from google.iam.v1 import iam_policy_pb2",
        "from google.iam.v1 import policy_pb2",
        "from google.protobuf import empty_pb2",
        "from google.protobuf import field_mask_pb2",
        "from google.protobuf import wrappers_pb2",
    ]
    for i in unused_imports:
        s.replace(
            f"google/cloud/storage_{version}/storage_client.py",
            f"{i}",
            ""
        )


# ----------------------------------------------------------------------------
# Add templated files
# ----------------------------------------------------------------------------
templated_files = common.py_library(
    cov_level=99,
    system_test_external_dependencies=[
        "google-cloud-iam",
        "google-cloud-pubsub < 2.0.0",
        # See: https://github.com/googleapis/python-storage/issues/226
        "google-cloud-kms < 2.0dev",
    ],
)
s.move(
    templated_files, excludes=["docs/multiprocessing.rst"],
)

s.shell.run(["nox", "-s", "blacken"], hide_output=False)
