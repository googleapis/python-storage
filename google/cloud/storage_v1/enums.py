# -*- coding: utf-8 -*-
#
# Copyright 2020 Google LLC
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

"""Wrappers for protocol buffer enum types."""

import enum


class CommonEnums(object):
    class PredefinedBucketAcl(enum.IntEnum):
        """
        Predefined or "canned" aliases for sets of specific bucket ACL entries.

        Attributes:
          PREDEFINED_BUCKET_ACL_UNSPECIFIED (int): No predefined ACL.
          BUCKET_ACL_AUTHENTICATED_READ (int): Project team owners get ``OWNER`` access, and
          ``allAuthenticatedUsers`` get ``READER`` access.
          BUCKET_ACL_PRIVATE (int): Project team owners get ``OWNER`` access.
          BUCKET_ACL_PROJECT_PRIVATE (int): Project team members get access according to their roles.
          BUCKET_ACL_PUBLIC_READ (int): Project team owners get ``OWNER`` access, and ``allUsers`` get
          ``READER`` access.
          BUCKET_ACL_PUBLIC_READ_WRITE (int): Project team owners get ``OWNER`` access, and ``allUsers`` get
          ``WRITER`` access.
        """

        PREDEFINED_BUCKET_ACL_UNSPECIFIED = 0
        BUCKET_ACL_AUTHENTICATED_READ = 1
        BUCKET_ACL_PRIVATE = 2
        BUCKET_ACL_PROJECT_PRIVATE = 3
        BUCKET_ACL_PUBLIC_READ = 4
        BUCKET_ACL_PUBLIC_READ_WRITE = 5

    class PredefinedObjectAcl(enum.IntEnum):
        """
        Predefined or "canned" aliases for sets of specific object ACL entries.

        Attributes:
          PREDEFINED_OBJECT_ACL_UNSPECIFIED (int): No predefined ACL.
          OBJECT_ACL_AUTHENTICATED_READ (int): Object owner gets ``OWNER`` access, and ``allAuthenticatedUsers``
          get ``READER`` access.
          OBJECT_ACL_BUCKET_OWNER_FULL_CONTROL (int): Object owner gets ``OWNER`` access, and project team owners get
          ``OWNER`` access.
          OBJECT_ACL_BUCKET_OWNER_READ (int): Object owner gets ``OWNER`` access, and project team owners get
          ``READER`` access.
          OBJECT_ACL_PRIVATE (int): Object owner gets ``OWNER`` access.
          OBJECT_ACL_PROJECT_PRIVATE (int): Object owner gets ``OWNER`` access, and project team members get
          access according to their roles.
          OBJECT_ACL_PUBLIC_READ (int): Object owner gets ``OWNER`` access, and ``allUsers`` get ``READER``
          access.
        """

        PREDEFINED_OBJECT_ACL_UNSPECIFIED = 0
        OBJECT_ACL_AUTHENTICATED_READ = 1
        OBJECT_ACL_BUCKET_OWNER_FULL_CONTROL = 2
        OBJECT_ACL_BUCKET_OWNER_READ = 3
        OBJECT_ACL_PRIVATE = 4
        OBJECT_ACL_PROJECT_PRIVATE = 5
        OBJECT_ACL_PUBLIC_READ = 6

    class Projection(enum.IntEnum):
        """
        A set of properties to return in a response.

        Attributes:
          PROJECTION_UNSPECIFIED (int): No specified projection.
          NO_ACL (int): Omit ``owner``, ``acl``, and ``defaultObjectAcl`` properties.
          FULL (int): Include all properties.
        """

        PROJECTION_UNSPECIFIED = 0
        NO_ACL = 1
        FULL = 2


class ServiceConstants(object):
    class Values(enum.IntEnum):
        """
        A collection of constant values meaningful to the Storage API.

        Attributes:
          VALUES_UNSPECIFIED (int): Unused. Proto3 requires first enum to be 0.
          MAX_READ_CHUNK_BYTES (int): The maximum size chunk that can will be returned in a single
          ReadRequest.
          2 MiB.
          MAX_WRITE_CHUNK_BYTES (int): The maximum size chunk that can be sent in a single InsertObjectRequest.
          2 MiB.
          MAX_OBJECT_SIZE_MB (int): The maximum size of an object in MB - whether written in a single stream
          or composed from multiple other objects.
          5 TiB.
          MAX_CUSTOM_METADATA_FIELD_NAME_BYTES (int): The maximum length field name that can be sent in a single
          custom metadata field.
          1 KiB.
          MAX_CUSTOM_METADATA_FIELD_VALUE_BYTES (int): The maximum length field value that can be sent in a single
          custom_metadata field. 4 KiB.
          MAX_CUSTOM_METADATA_TOTAL_SIZE_BYTES (int): The maximum total bytes that can be populated into all field names
          and values of the custom_metadata for one object. 8 KiB.
          MAX_BUCKET_METADATA_TOTAL_SIZE_BYTES (int): The maximum total bytes that can be populated into all bucket metadata
          fields.
          20 KiB.
          MAX_NOTIFICATION_CONFIGS_PER_BUCKET (int): The maximum number of NotificationConfigurations that can be registered
          for a given bucket.
          MAX_LIFECYCLE_RULES_PER_BUCKET (int): The maximum number of LifecycleRules that can be registered for a given
          bucket.
          MAX_NOTIFICATION_CUSTOM_ATTRIBUTES (int): The maximum number of custom attributes per NotificationConfig.
          MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_KEY_LENGTH (int): The maximum length of a custom attribute key included in
          NotificationConfig.
          MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_VALUE_LENGTH (int): The maximum length of a custom attribute value included in a
          NotificationConfig.
          MAX_LABELS_ENTRIES_COUNT (int): The maximum number of key/value entries per bucket label.
          MAX_LABELS_KEY_VALUE_LENGTH (int): The maximum character length of the key or value in a bucket
          label map.
          MAX_LABELS_KEY_VALUE_BYTES (int): The maximum byte size of the key or value in a bucket label
          map.
          MAX_OBJECT_IDS_PER_DELETE_OBJECTS_REQUEST (int): The maximum number of object IDs that can be included in a
          DeleteObjectsRequest.
          SPLIT_TOKEN_MAX_VALID_DAYS (int): The maximum number of days for which a token returned by the
          GetListObjectsSplitPoints RPC is valid.
        """

        VALUES_UNSPECIFIED = 0
        MAX_READ_CHUNK_BYTES = 2097152
        MAX_WRITE_CHUNK_BYTES = 2097152
        MAX_OBJECT_SIZE_MB = 5242880
        MAX_CUSTOM_METADATA_FIELD_NAME_BYTES = 1024
        MAX_CUSTOM_METADATA_FIELD_VALUE_BYTES = 4096
        MAX_CUSTOM_METADATA_TOTAL_SIZE_BYTES = 8192
        MAX_BUCKET_METADATA_TOTAL_SIZE_BYTES = 20480
        MAX_NOTIFICATION_CONFIGS_PER_BUCKET = 100
        MAX_LIFECYCLE_RULES_PER_BUCKET = 100
        MAX_NOTIFICATION_CUSTOM_ATTRIBUTES = 5
        MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_KEY_LENGTH = 256
        MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_VALUE_LENGTH = 1024
        MAX_LABELS_ENTRIES_COUNT = 64
        MAX_LABELS_KEY_VALUE_LENGTH = 63
        MAX_LABELS_KEY_VALUE_BYTES = 128
        MAX_OBJECT_IDS_PER_DELETE_OBJECTS_REQUEST = 1000
        SPLIT_TOKEN_MAX_VALID_DAYS = 14
