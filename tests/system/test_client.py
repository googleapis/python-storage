# Copyright 2021 Google LLC
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

import re

import pytest

from  . import _helpers


def test_get_service_account_email(storage_client):
    _helpers.require_service_account(storage_client)

    domain = "gs-project-accounts.iam.gserviceaccount.com"
    email = storage_client.get_service_account_email()

    new_style = re.compile(r"service-(?P<projnum>[^@]+)@{}".format(domain))
    old_style = re.compile(r"{}@{}".format(storage_client.project, domain))
    patterns = [new_style, old_style]
    matches = [pattern.match(email) for pattern in patterns]

    assert any(match for match in matches if match is not None)
