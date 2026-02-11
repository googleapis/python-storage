# Copyright 2026 Google LLC
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
"""The abstract for python-storage Blob."""

import abc


class BaseBlob(abc.ABC):
    """The abstract for python-storage Blob"""

    @property
    @abc.abstractmethod
    def encryption_key(self):
        """Retrieve the customer-supplied encryption key for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @encryption_key.setter
    @abc.abstractmethod
    def encryption_key(self, value):
        """Set the blob's encryption key."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def chunk_size(self):
        """Get the blob's default chunk size."""
        raise NotImplementedError("Not Yet Implemented")

    @chunk_size.setter
    @abc.abstractmethod
    def chunk_size(self, value):
        """Set the blob's default chunk size."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def metadata(self):
        """Retrieve arbitrary/application specific metadata for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @metadata.setter
    @abc.abstractmethod
    def metadata(self, value):
        """Update arbitrary/application specific metadata for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def kms_key_name(self):
        """Resource name of Cloud KMS key used to encrypt the blob's contents."""
        raise NotImplementedError("Not Yet Implemented")

    @kms_key_name.setter
    @abc.abstractmethod
    def kms_key_name(self, value):
        """Set KMS encryption key for object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def custom_time(self):
        """Retrieve the custom time for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @custom_time.setter
    @abc.abstractmethod
    def custom_time(self, value):
        """Set the custom time for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def bucket(self):
        """Bucket which contains the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def acl(self):
        """Create our ACL on demand."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def path(self):
        """Getter property for the URL path to this Blob."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def client(self):
        """The client bound to this blob."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def user_project(self):
        """Project ID billed for API requests made via this blob."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def public_url(self):
        """The public URL for this blob."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def component_count(self):
        """Number of underlying components that make up this object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def etag(self):
        """Retrieve the ETag for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def generation(self):
        """Retrieve the generation for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def id(self):
        """Retrieve the ID for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def media_link(self):
        """Retrieve the media download URI for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def metageneration(self):
        """Retrieve the metageneration for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def owner(self):
        """Retrieve info about the owner of the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def retention_expiration_time(self):
        """Retrieve timestamp at which the object's retention period expires."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def self_link(self):
        """Retrieve the URI for the object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def size(self):
        """Size of the object, in bytes."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def time_deleted(self):
        """Retrieve the timestamp at which the object was deleted."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def time_created(self):
        """Retrieve the timestamp at which the object was created."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def updated(self):
        """Retrieve the timestamp at which the object was updated."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def retention(self):
        """Retrieve the retention configuration for this object."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def soft_delete_time(self):
        """If this object has been soft-deleted, returns the time at which it became soft-deleted."""
        raise NotImplementedError("Not Yet Implemented")

    @property
    @abc.abstractmethod
    def hard_delete_time(self):
        """If this object has been soft-deleted, returns the time at which it will be permanently deleted."""
        raise NotImplementedError("Not Yet Implemented")

    @abc.abstractmethod
    def reload(
        self,
        client=None,
        projection="noAcl",
        if_etag_match=None,
        if_etag_not_match=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
        retry=None,
        soft_deleted=None,
    ):
        raise NotImplementedError("Not Yet Implemented.")

    @abc.abstractmethod
    def open(
        self,
        mode="r",
        chunk_size=None,
        ignore_flush=None,
        encoding=None,
        errors=None,
        newline=None,
        **kwargs,
    ):
        """Create a file handler for file-like I/O to or from this blob."""
        raise NotImplementedError("Not Yet Implemented")
