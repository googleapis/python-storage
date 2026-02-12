import pytest
from unittest import mock

from google.cloud.storage.abstracts.base_blob import BaseBlob


@pytest.fixture
def base_blob():
    # Temporarily remove abstract methods restriction to allow direct instantiation
    with mock.patch.object(BaseBlob, "__abstractmethods__", set()):
        yield BaseBlob()


# Properties that have both getters and setters
READ_WRITE_PROPS = [
    "encryption_key",
    "chunk_size",
    "metadata",
    "kms_key_name",
    "custom_time",
]

# Properties that only have getters
READ_ONLY_PROPS = [
    "bucket",
    "acl",
    "path",
    "client",
    "user_project",
    "public_url",
    "component_count",
    "etag",
    "generation",
    "id",
    "media_link",
    "metageneration",
    "owner",
    "retention_expiration_time",
    "self_link",
    "size",
    "time_deleted",
    "time_created",
    "updated",
    "retention",
    "soft_delete_time",
    "hard_delete_time",
]


@pytest.mark.parametrize("prop", READ_WRITE_PROPS + READ_ONLY_PROPS)
def test_property_getters(base_blob, prop):
    with pytest.raises(NotImplementedError, match="Not Yet Implemented"):
        getattr(base_blob, prop)


@pytest.mark.parametrize("prop", READ_WRITE_PROPS)
def test_property_setters(base_blob, prop):
    with pytest.raises(NotImplementedError, match="Not Yet Implemented"):
        setattr(base_blob, prop, "dummy_value")


def test_reload(base_blob):
    with pytest.raises(NotImplementedError, match="Not Yet Implemented"):
        base_blob.reload()


def test_open(base_blob):
    with pytest.raises(NotImplementedError, match="Not Yet Implemented"):
        base_blob.open()
