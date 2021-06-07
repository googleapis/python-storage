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

import re

import synthtool as s
from synthtool import gcp

common = gcp.CommonTemplates()

# ----------------------------------------------------------------------------
# Add templated files
# ----------------------------------------------------------------------------
templated_files = common.py_library(
    cov_level=100,
    system_test_external_dependencies=[
        "google-cloud-iam",
        "google-cloud-pubsub < 2.0.0",
        # See: https://github.com/googleapis/python-storage/issues/226
        "google-cloud-kms < 2.0dev",
    ],
)

s.move(
    templated_files, excludes=["docs/multiprocessing.rst", "noxfile.py", "CONTRIBUTING.rst"],
)

s.replace(
    "docs/conf.py",
    """\
intersphinx_mapping = {
    "python": ("https://python.readthedocs.org/en/latest/", None),
""",
    """\
intersphinx_mapping = {
    "python": ("https://python.readthedocs.org/en/latest/", None),
    "requests": ("https://docs.python-requests.org/en/master/", None),
""",
)

s.shell.run(["nox", "-s", "blacken"], hide_output=False)
