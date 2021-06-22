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

import pytest

from google.api_core import exceptions
from . import _helpers


def test_bucket_create_w_alt_storage_class(storage_client, buckets_to_delete):
    from google.cloud.storage import constants

    new_bucket_name = _helpers.unique_name("bucket-w-archive")

    with pytest.raises(exceptions.NotFound):
        storage_client.get_bucket(new_bucket_name)

    bucket = storage_client.bucket(new_bucket_name)
    bucket.storage_class = constants.ARCHIVE_STORAGE_CLASS

    _helpers.retry_429_503(bucket.create)()
    buckets_to_delete.append(bucket)

    created = storage_client.get_bucket(new_bucket_name)
    assert created.storage_class == constants.ARCHIVE_STORAGE_CLASS


def test_bucket_lifecycle_rules(storage_client, buckets_to_delete):
    from google.cloud.storage import constants
    from google.cloud.storage.bucket import LifecycleRuleDelete
    from google.cloud.storage.bucket import LifecycleRuleSetStorageClass

    new_bucket_name = _helpers.unique_name("w-lifcycle-rules")
    custom_time_before = datetime.date(2018, 8, 1)
    noncurrent_before = datetime.date(2018, 8, 1)

    with pytest.raises(exceptions.NotFound):
        storage_client.get_bucket(new_bucket_name)

    bucket = storage_client.bucket(new_bucket_name)
    bucket.add_lifecycle_delete_rule(
        age=42,
        number_of_newer_versions=3,
        days_since_custom_time=2,
        custom_time_before=custom_time_before,
        days_since_noncurrent_time=2,
        noncurrent_time_before=noncurrent_before,
    )
    bucket.add_lifecycle_set_storage_class_rule(
        constants.COLDLINE_STORAGE_CLASS,
        is_live=False,
        matches_storage_class=[constants.NEARLINE_STORAGE_CLASS],
    )

    expected_rules = [
        LifecycleRuleDelete(
            age=42,
            number_of_newer_versions=3,
            days_since_custom_time=2,
            custom_time_before=custom_time_before,
            days_since_noncurrent_time=2,
            noncurrent_time_before=noncurrent_before,
        ),
        LifecycleRuleSetStorageClass(
            constants.COLDLINE_STORAGE_CLASS,
            is_live=False,
            matches_storage_class=[constants.NEARLINE_STORAGE_CLASS],
        ),
    ]

    _helpers.retry_429_503(bucket.create)(location="us")
    buckets_to_delete.append(bucket)

    assert bucket.name == new_bucket_name
    assert list(bucket.lifecycle_rules) == expected_rules

    bucket.clear_lifecyle_rules()
    bucket.patch()

    assert list(bucket.lifecycle_rules) == []


def test_bucket_update_labels(storage_client, buckets_to_delete):
    bucket_name = _helpers.unique_name("update-labels")
    bucket = _helpers.retry_429_503(storage_client.create_bucket)(bucket_name)
    buckets_to_delete.append(bucket)
    assert bucket.exists()

    updated_labels = {"test-label": "label-value"}
    bucket.labels = updated_labels
    bucket.update()
    assert bucket.labels == updated_labels

    new_labels = {"another-label": "another-value"}
    bucket.labels = new_labels
    bucket.patch()
    assert bucket.labels == new_labels

    bucket.labels = {}
    bucket.update()
    assert bucket.labels == {}


def test_bucket_get_set_iam_policy(
    storage_client, buckets_to_delete, service_account,
):
    from google.cloud.storage.iam import STORAGE_OBJECT_VIEWER_ROLE
    from google.api_core.exceptions import BadRequest
    from google.api_core.exceptions import PreconditionFailed

    bucket_name = _helpers.unique_name("iam-policy")
    bucket = _helpers.retry_429_503(storage_client.create_bucket)(bucket_name)
    buckets_to_delete.append(bucket)
    assert bucket.exists()

    policy_no_version = bucket.get_iam_policy()
    assert policy_no_version.version == 1

    policy = bucket.get_iam_policy(requested_policy_version=3)
    assert policy == policy_no_version

    member = "serviceAccount:{}".format(storage_client.get_service_account_email())

    binding_w_condition = {
        "role": STORAGE_OBJECT_VIEWER_ROLE,
        "members": {member},
        "condition": {
            "title": "always-true",
            "description": "test condition always-true",
            "expression": "true",
        },
    }
    policy.bindings.append(binding_w_condition)

    with pytest.raises(PreconditionFailed, match="enable uniform bucket-level access"):
        bucket.set_iam_policy(policy)

    bucket.iam_configuration.uniform_bucket_level_access_enabled = True
    bucket.patch()

    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.bindings.append(binding_w_condition)

    with pytest.raises(BadRequest, match="at least 3"):
        bucket.set_iam_policy(policy)

    policy.version = 3
    returned_policy = bucket.set_iam_policy(policy)
    assert returned_policy.version == 3
    assert returned_policy.bindings == policy.bindings

    fetched_policy = bucket.get_iam_policy(requested_policy_version=3)
    assert fetched_policy.bindings == returned_policy.bindings


def test_bucket_crud_w_requester_pays(storage_client, buckets_to_delete, user_project):
    new_bucket_name = _helpers.unique_name("w-requester-pays")
    created = _helpers.retry_429_503(storage_client.create_bucket)(
        new_bucket_name, requester_pays=True
    )
    buckets_to_delete.append(created)
    assert created.name == new_bucket_name
    assert created.requester_pays

    with_user_project = storage_client.bucket(
        new_bucket_name, user_project=user_project,
    )

    try:
        # Exercise 'buckets.get' w/ userProject.
        assert with_user_project.exists()
        with_user_project.reload()
        assert with_user_project.requester_pays

        # Exercise 'buckets.patch' w/ userProject.
        with_user_project.configure_website(
            main_page_suffix="index.html", not_found_page="404.html"
        )
        with_user_project.patch()
        expected_website = {"mainPageSuffix": "index.html", "notFoundPage": "404.html"}
        assert with_user_project._properties["website"] == expected_website

        # Exercise 'buckets.update' w/ userProject.
        new_labels = {"another-label": "another-value"}
        with_user_project.labels = new_labels
        with_user_project.update()
        assert with_user_project.labels == new_labels

    finally:
        # Exercise 'buckets.delete' w/ userProject.
        with_user_project.delete()
        buckets_to_delete.remove(created)


def test_bucket_acls_iam_w_user_project(
    storage_client, buckets_to_delete, user_project
):
    new_bucket_name = _helpers.unique_name("acl-w-user-project")
    created = _helpers.retry_429_503(storage_client.create_bucket)(
        new_bucket_name, requester_pays=True,
    )
    buckets_to_delete.append(created)

    with_user_project = storage_client.bucket(
        new_bucket_name, user_project=user_project
    )

    # Exercise bucket ACL w/ userProject
    acl = with_user_project.acl
    acl.reload()
    acl.all().grant_read()
    acl.save()
    assert "READER" in acl.all().get_roles()

    del acl.entities["allUsers"]
    acl.save()
    assert not acl.has_entity("allUsers")

    # Exercise default object ACL w/ userProject
    doa = with_user_project.default_object_acl
    doa.reload()
    doa.all().grant_read()
    doa.save()
    assert "READER" in doa.all().get_roles()

    # Exercise IAM w/ userProject
    test_permissions = ["storage.buckets.get"]
    found = with_user_project.test_iam_permissions(test_permissions)
    assert found == test_permissions

    policy = with_user_project.get_iam_policy()
    viewers = policy.setdefault("roles/storage.objectViewer", set())
    viewers.add(policy.all_users())
    with_user_project.set_iam_policy(policy)


def test_bucket_copy_blob_w_user_project(
    storage_client, buckets_to_delete, blobs_to_delete, user_project,
):
    payload = b"DEADBEEF"
    new_bucket_name = _helpers.unique_name("copy-w-requester-pays")
    created = _helpers.retry_429_503(storage_client.create_bucket)(
        new_bucket_name, requester_pays=True
    )
    buckets_to_delete.append(created)
    assert created.name == new_bucket_name
    assert created.requester_pays

    blob = created.blob("simple")
    blob.upload_from_string(payload)
    blobs_to_delete.append(blob)

    with_user_project = storage_client.bucket(
        new_bucket_name, user_project=user_project
    )

    new_blob = _helpers.retry_bad_copy(with_user_project.copy_blob)(
        blob, with_user_project, "simple-copy"
    )
    blobs_to_delete.append(new_blob)

    assert new_blob.download_as_bytes() == payload


def test_bucket_copy_blob_w_generation_match(
    storage_client, buckets_to_delete, blobs_to_delete,
):
    payload = b"DEADBEEF"
    new_bucket_name = _helpers.unique_name("generation-match")
    created = _helpers.retry_429_503(storage_client.create_bucket)(
        new_bucket_name, requester_pays=True
    )
    buckets_to_delete.append(created)
    assert created.name == new_bucket_name

    blob = created.blob("simple")
    blob.upload_from_string(payload)
    blobs_to_delete.append(blob)

    dest_bucket = storage_client.bucket(new_bucket_name)

    new_blob = dest_bucket.copy_blob(
        blob, dest_bucket, "simple-copy", if_source_generation_match=blob.generation,
    )
    blobs_to_delete.append(new_blob)

    assert new_blob.download_as_bytes() == payload


def test_bucket_copy_blob_w_metageneration_match(
    storage_client, buckets_to_delete, blobs_to_delete,
):
    payload = b"DEADBEEF"
    new_bucket_name = _helpers.unique_name("generation-match")
    created = _helpers.retry_429_503(storage_client.create_bucket)(
        new_bucket_name, requester_pays=True
    )
    buckets_to_delete.append(created)
    assert created.name == new_bucket_name

    blob = created.blob("simple")
    blob.upload_from_string(payload)
    blobs_to_delete.append(blob)

    dest_bucket = storage_client.bucket(new_bucket_name)

    new_blob = dest_bucket.copy_blob(
        blob,
        dest_bucket,
        "simple-copy",
        if_source_metageneration_match=blob.metageneration,
    )
    blobs_to_delete.append(new_blob)

    assert new_blob.download_as_bytes() == payload


def test_bucket_get_blob_with_user_project(
    storage_client, buckets_to_delete, blobs_to_delete, user_project,
):
    blob_name = "blob-name"
    payload = b"DEADBEEF"
    new_bucket_name = _helpers.unique_name("w-requester-pays")
    created = _helpers.retry_429_503(storage_client.create_bucket)(
        new_bucket_name, requester_pays=True
    )
    buckets_to_delete.append(created)
    assert created.name == new_bucket_name
    assert created.requester_pays

    with_user_project = storage_client.bucket(
        new_bucket_name, user_project=user_project
    )

    assert with_user_project.get_blob("nonesuch") is None

    to_add = created.blob(blob_name)
    to_add.upload_from_string(payload)
    blobs_to_delete.append(to_add)

    found = with_user_project.get_blob(blob_name)
    assert found.download_as_bytes() == payload
