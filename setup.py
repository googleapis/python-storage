# Copyright 2018 Google LLC
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

import io
import os

import setuptools


# Package metadata.

name = "google-cloud-storage"
description = "Google Cloud Storage API client library"
# Should be one of:
# 'Development Status :: 3 - Alpha'
# 'Development Status :: 4 - Beta'
# 'Development Status :: 5 - Production/Stable'
release_status = "Development Status :: 5 - Production/Stable"
dependencies = [
    "google-auth >= 1.25.0, < 2.0dev; python_version<'3.0'",
    "google-auth >= 1.25.0, < 3.0dev; python_version>='3.6'",
    "google-api-core >= 1.29.0, < 2.0dev; python_version<'3.0'",
    "google-api-core >= 1.29.0, < 3.0dev; python_version>='3.6'",
    "google-cloud-core >= 1.6.0, < 2.0dev; python_version<'3.0'",
    "google-cloud-core >= 1.6.0, < 3.0dev; python_version>='3.6'",
    "google-resumable-media >= 1.3.0, < 2.0dev; python_version<'3.0'",
    "google-resumable-media >= 1.3.0, < 3.0dev; python_version>='3.6'",
    "requests >= 2.18.0, < 3.0.0dev",
    "protobuf < 3.18.0; python_version<'3.0'",
    "protobuf; python_version>='3.6'",
    "googleapis-common-protos < 1.53.0; python_version<'3.0'",
    "six",
]
extras = {}


# Setup boilerplate below this line.

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "google/cloud/storage/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

readme_filename = os.path.join(package_root, "README.rst")
with io.open(readme_filename, encoding="utf-8") as readme_file:
    readme = readme_file.read()

# Only include packages under the 'google' namespace. Do not include tests,
# benchmarks, etc.
packages = [
    package for package in setuptools.find_packages() if package.startswith("google")
]

# Determine which namespaces are needed.
namespaces = ["google"]
if "google.cloud" in packages:
    namespaces.append("google.cloud")


setuptools.setup(
    name=name,
    version=version,
    description=description,
    long_description=readme,
    author="Google LLC",
    author_email="googleapis-packages@google.com",
    license="Apache 2.0",
    url="https://github.com/googleapis/python-storage",
    classifiers=[
        release_status,
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Topic :: Internet",
    ],
    platforms="Posix; MacOS X; Windows",
    packages=packages,
    namespace_packages=namespaces,
    install_requires=dependencies,
    extras_require=extras,
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*",
    include_package_data=True,
    zip_safe=False,
)
