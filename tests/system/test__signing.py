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

import datetime
import time

import requests


def _morph_expiration(version, expiration):
    if expiration is not None:
        return expiration

    if version == "v2":
        return int(time.time()) + 10

    return 10


def _create_signed_list_blobs_url_helper(
    client, bucket, version, expiration=None, method="GET"
):
    expiration = _morph_expiration(version, expiration)

    signed_url = bucket.generate_signed_url(
        expiration=expiration, method=method, client=client, version=version
    )

    response = requests.get(signed_url)
    assert response.status_code == 200


def test_create_signed_list_blobs_url_v2(storage_client, signing_bucket):
    _create_signed_list_blobs_url_helper(
        storage_client, signing_bucket, version="v2",
    )


def test_create_signed_list_blobs_url_v2_w_expiration(storage_client, signing_bucket):
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=10)

    _create_signed_list_blobs_url_helper(
        storage_client, signing_bucket, expiration=now + delta, version="v2",
    )


def test_create_signed_list_blobs_url_v4(storage_client, signing_bucket):
    _create_signed_list_blobs_url_helper(
        storage_client, signing_bucket, version="v4",
    )


def test_create_signed_list_blobs_url_v4_w_expiration(storage_client, signing_bucket):
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=10)
    _create_signed_list_blobs_url_helper(
        storage_client, signing_bucket, expiration=now + delta, version="v4",
    )
