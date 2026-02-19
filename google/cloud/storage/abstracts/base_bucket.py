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
"""The abstract for python-storage Bucket."""

import abc


class BaseBucket(abc.ABC):
    """The abstract for python-storage Bucket"""

    @property
    @abc.abstractmethod
    def rpo(self):
        """Get the RPO (Recovery Point Objective) of this bucket"""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def retention_period(self):
        """Retrieve or set the retention period for items in the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @retention_period.setter
    @abc.abstractmethod
    def retention_period(self, value):
        """Set the retention period for items in the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def storage_class(self):
        """Retrieve or set the storage class for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @storage_class.setter
    @abc.abstractmethod
    def storage_class(self, value):
        """Set the storage class for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def versioning_enabled(self):
        """Is versioning enabled for this bucket?"""
        raise NotImplementedError("Not yet Implemented")

    @versioning_enabled.setter
    @abc.abstractmethod
    def versioning_enabled(self, value):
        """Enable versioning for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def requester_pays(self):
        """Does the requester pay for API requests for this bucket?"""
        raise NotImplementedError("Not yet Implemented")

    @requester_pays.setter
    @abc.abstractmethod
    def requester_pays(self, value):
        """Update whether requester pays for API requests for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def autoclass_enabled(self):
        """Whether Autoclass is enabled for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @autoclass_enabled.setter
    @abc.abstractmethod
    def autoclass_enabled(self, value):
        """Enable or disable Autoclass at the bucket-level."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def autoclass_terminal_storage_class(self):
        """The storage class that objects in an Autoclass bucket eventually transition to if
        they are not read for a certain length of time. Valid values are NEARLINE and ARCHIVE.
        """
        raise NotImplementedError("Not yet Implemented")

    @autoclass_terminal_storage_class.setter
    @abc.abstractmethod
    def autoclass_terminal_storage_class(self, value):
        """The storage class that objects in an Autoclass bucket eventually transition to if
        they are not read for a certain length of time. Valid values are NEARLINE and ARCHIVE.
        """
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def hierarchical_namespace_enabled(self):
        """Whether hierarchical namespace is enabled for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @hierarchical_namespace_enabled.setter
    @abc.abstractmethod
    def hierarchical_namespace_enabled(self, value):
        """Enable or disable hierarchical namespace at the bucket-level."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def cors(self):
        """Retrieve or set CORS policies configured for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @cors.setter
    @abc.abstractmethod
    def cors(self, entries):
        """Set CORS policies configured for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def default_kms_key_name(self):
        """Retrieve / set default KMS encryption key for objects in the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @default_kms_key_name.setter
    @abc.abstractmethod
    def default_kms_key_name(self, value):
        """Set default KMS encryption key for objects in the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def labels(self):
        """Retrieve or set labels assigned to this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @labels.setter
    @abc.abstractmethod
    def labels(self, mapping):
        """Set labels assigned to this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def ip_filter(self):
        """Retrieve or set the IP Filter configuration for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @ip_filter.setter
    @abc.abstractmethod
    def ip_filter(self, value):
        """Retrieve or set the IP Filter configuration for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def lifecycle_rules(self):
        """Retrieve or set lifecycle rules configured for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @lifecycle_rules.setter
    @abc.abstractmethod
    def lifecycle_rules(self, rules):
        """Set lifecycle rules configured for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def location(self):
        """Retrieve location configured for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @location.setter
    @abc.abstractmethod
    def location(self, value):
        """(Deprecated) Set `Bucket.location`"""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def generation(self):
        """Retrieve the generation for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def soft_delete_time(self):
        """If this bucket has been soft-deleted, returns the time at which it became soft-deleted."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def hard_delete_time(self):
        """If this bucket has been soft-deleted, returns the time at which it will be permanently deleted."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def autoclass_terminal_storage_class_update_time(self):
        """The time at which the Autoclass terminal_storage_class field was last updated for this bucket"""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def object_retention_mode(self):
        """Retrieve the object retention mode set on the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def user_project(self):
        """Project ID to be billed for API requests made via this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def autoclass_toggle_time(self):
        """Retrieve the toggle time when Autoclaass was last enabled or disabled for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def time_created(self):
        """Retrieve the timestamp at which the bucket was created."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def updated(self):
        """Retrieve the timestamp at which the bucket was last updated."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def acl(self):
        """Create our ACL on demand."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def default_object_acl(self):
        """Create our defaultObjectACL on demand."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def etag(self):
        """Retrieve the ETag for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def id(self):
        """Retrieve the ID for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def iam_configuration(self):
        """Retrieve IAM configuration for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def soft_delete_policy(self):
        """Retrieve the soft delete policy for this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def data_locations(self):
        """Retrieve the list of regional locations for custom dual-region buckets."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def location_type(self):
        """Retrieve the location type for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def path(self):
        """The URL path to this bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def metageneration(self):
        """Retrieve the metageneration for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def owner(self):
        """Retrieve info about the owner of the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def project_number(self):
        """Retrieve the number of the project to which the bucket is assigned."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def retention_policy_effective_time(self):
        """Retrieve the effective time of the bucket's retention policy."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def retention_policy_locked(self):
        """Retrieve whthere the bucket's retention policy is locked."""
        raise NotImplementedError("Not yet Implemented")

    @property
    @abc.abstractmethod
    def self_link(self):
        """Retrieve the URI for the bucket."""
        raise NotImplementedError("Not yet Implemented")

    @abc.abstractmethod
    def reload(
        self,
        client=None,
        projection="noAcl",
        timeout=None,
        if_etag_match=None,
        if_etag_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        retry=None,
        soft_deleted=None,
    ):
        """Load the bucket metadata into bucket instance."""
        raise NotImplementedError("Not Implemented Yet")

    @abc.abstractmethod
    def patch(
        self,
        client=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
        retry=None,
    ):
        """Patch the bucket metadata into bucket instance."""
        raise NotImplementedError("Not Implemented Yet")

    @abc.abstractmethod
    def blob(
        self,
        blob_name,
        chunk_size=None,
        encryption_key=None,
        kms_key_name=None,
        generation=None,
    ):
        """Factory constructor for blob object."""
        raise NotImplementedError("Not Implemented Yet")

    @abc.abstractmethod
    def get_blob(
        self,
        blob_name,
        client=None,
        encryption_key=None,
        generation=None,
        if_etag_match=None,
        if_etag_not_match=None,
        if_generation_match=None,
        if_generation_not_match=None,
        if_metageneration_match=None,
        if_metageneration_not_match=None,
        timeout=None,
        retry=None,
        soft_deleted=None,
        **kwargs,
    ):
        """Get a blob object by name."""
        raise NotImplementedError("Not Implemented Yet")
