import pytest
from unittest import mock

from google.cloud.storage.abstracts.base_bucket import BaseBucket


@pytest.fixture
def base_bucket():
    # Temporarily remove abstract methods restriction to allow direct instantiation
    with mock.patch.object(BaseBucket, "__abstractmethods__", set()):
        yield BaseBucket()


# Properties that have both getters and setters
READ_WRITE_PROPS = [
    "retention_period",
    "storage_class",
    "versioning_enabled",
    "requester_pays",
    "autoclass_enabled",
    "autoclass_terminal_storage_class",
    "hierarchical_namespace_enabled",
    "cors",
    "default_kms_key_name",
    "labels",
    "ip_filter",
    "lifecycle_rules",
    "location",
]

# Properties that only have getters
READ_ONLY_PROPS = [
    "rpo",
    "generation",
    "soft_delete_time",
    "hard_delete_time",
    "autoclass_terminal_storage_class_update_time",
    "object_retention_mode",
    "user_project",
    "autoclass_toggle_time",
    "time_created",
    "updated",
    "acl",
    "default_object_acl",
    "etag",
    "id",
    "iam_configuration",
    "soft_delete_policy",
    "data_locations",
    "location_type",
    "path",
    "metageneration",
    "owner",
    "project_number",
    "retention_policy_effective_time",
    "retention_policy_locked",
    "self_link",
]


@pytest.mark.parametrize("prop", READ_WRITE_PROPS + READ_ONLY_PROPS)
def test_property_getters(base_bucket, prop):
    with pytest.raises(NotImplementedError):
        getattr(base_bucket, prop)


@pytest.mark.parametrize("prop", READ_WRITE_PROPS)
def test_property_setters(base_bucket, prop):
    with pytest.raises(NotImplementedError):
        setattr(base_bucket, prop, "dummy_value")


def test_reload(base_bucket):
    with pytest.raises(NotImplementedError):
        base_bucket.reload()


def test_patch(base_bucket):
    with pytest.raises(NotImplementedError):
        base_bucket.patch()


def test_blob(base_bucket):
    with pytest.raises(NotImplementedError):
        base_bucket.blob("dummy_blob_name")


def test_get_blob(base_bucket):
    with pytest.raises(NotImplementedError):
        base_bucket.get_blob("dummy_blob_name")
