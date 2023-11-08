# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import sys
import tempfile


def test_namespace_package_compat():
    """
    The ``google`` namespace package should not be masked
    by the presence of this package.
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        google = tmp_path + "/google"
        os.mkdir(google)
        path = os.path.join(google, "othermod.py")
        with open(path, "w") as f:
            f.write("pass")
        env = dict(os.environ, PYTHONPATH=tmp_path)
        cmd = [sys.executable, "-m", "google.othermod"]
        subprocess.check_call(cmd, env=env)
