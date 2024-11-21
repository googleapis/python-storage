# Copyright 2017 Google Inc.
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

"""Common utilities for Google Media Downloads and Resumable Uploads.

Includes custom exception types, useful constants and shared helpers.
"""

import http.client

UPLOAD_CHUNK_SIZE = 262144  # 256 * 1024
"""int: Chunks in a resumable upload must come in multiples of 256 KB."""