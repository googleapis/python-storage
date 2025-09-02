# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
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
#
from google.cloud.storage import gapic_version as package_version

__version__ = package_version.__version__


from google.cloud.storage_v2.services.storage.client import StorageClient
from google.cloud.storage_v2.services.storage.async_client import StorageAsyncClient

from google.cloud.storage_v2.types.storage import AppendObjectSpec
from google.cloud.storage_v2.types.storage import BidiReadHandle
from google.cloud.storage_v2.types.storage import BidiReadObjectError
from google.cloud.storage_v2.types.storage import BidiReadObjectRedirectedError
from google.cloud.storage_v2.types.storage import BidiReadObjectRequest
from google.cloud.storage_v2.types.storage import BidiReadObjectResponse
from google.cloud.storage_v2.types.storage import BidiReadObjectSpec
from google.cloud.storage_v2.types.storage import BidiWriteHandle
from google.cloud.storage_v2.types.storage import BidiWriteObjectRedirectedError
from google.cloud.storage_v2.types.storage import BidiWriteObjectRequest
from google.cloud.storage_v2.types.storage import BidiWriteObjectResponse
from google.cloud.storage_v2.types.storage import Bucket
from google.cloud.storage_v2.types.storage import BucketAccessControl
from google.cloud.storage_v2.types.storage import CancelResumableWriteRequest
from google.cloud.storage_v2.types.storage import CancelResumableWriteResponse
from google.cloud.storage_v2.types.storage import ChecksummedData
from google.cloud.storage_v2.types.storage import CommonObjectRequestParams
from google.cloud.storage_v2.types.storage import ComposeObjectRequest
from google.cloud.storage_v2.types.storage import ContentRange
from google.cloud.storage_v2.types.storage import CreateBucketRequest
from google.cloud.storage_v2.types.storage import CustomerEncryption
from google.cloud.storage_v2.types.storage import DeleteBucketRequest
from google.cloud.storage_v2.types.storage import DeleteObjectRequest
from google.cloud.storage_v2.types.storage import GetBucketRequest
from google.cloud.storage_v2.types.storage import GetObjectRequest
from google.cloud.storage_v2.types.storage import ListBucketsRequest
from google.cloud.storage_v2.types.storage import ListBucketsResponse
from google.cloud.storage_v2.types.storage import ListObjectsRequest
from google.cloud.storage_v2.types.storage import ListObjectsResponse
from google.cloud.storage_v2.types.storage import LockBucketRetentionPolicyRequest
from google.cloud.storage_v2.types.storage import MoveObjectRequest
from google.cloud.storage_v2.types.storage import Object
from google.cloud.storage_v2.types.storage import ObjectAccessControl
from google.cloud.storage_v2.types.storage import ObjectChecksums
from google.cloud.storage_v2.types.storage import ObjectContexts
from google.cloud.storage_v2.types.storage import ObjectCustomContextPayload
from google.cloud.storage_v2.types.storage import ObjectRangeData
from google.cloud.storage_v2.types.storage import Owner
from google.cloud.storage_v2.types.storage import ProjectTeam
from google.cloud.storage_v2.types.storage import QueryWriteStatusRequest
from google.cloud.storage_v2.types.storage import QueryWriteStatusResponse
from google.cloud.storage_v2.types.storage import ReadObjectRequest
from google.cloud.storage_v2.types.storage import ReadObjectResponse
from google.cloud.storage_v2.types.storage import ReadRange
from google.cloud.storage_v2.types.storage import ReadRangeError
from google.cloud.storage_v2.types.storage import RestoreObjectRequest
from google.cloud.storage_v2.types.storage import RewriteObjectRequest
from google.cloud.storage_v2.types.storage import RewriteResponse
from google.cloud.storage_v2.types.storage import ServiceConstants
from google.cloud.storage_v2.types.storage import StartResumableWriteRequest
from google.cloud.storage_v2.types.storage import StartResumableWriteResponse
from google.cloud.storage_v2.types.storage import UpdateBucketRequest
from google.cloud.storage_v2.types.storage import UpdateObjectRequest
from google.cloud.storage_v2.types.storage import WriteObjectRequest
from google.cloud.storage_v2.types.storage import WriteObjectResponse
from google.cloud.storage_v2.types.storage import WriteObjectSpec

__all__ = ('StorageClient',
    'StorageAsyncClient',
    'AppendObjectSpec',
    'BidiReadHandle',
    'BidiReadObjectError',
    'BidiReadObjectRedirectedError',
    'BidiReadObjectRequest',
    'BidiReadObjectResponse',
    'BidiReadObjectSpec',
    'BidiWriteHandle',
    'BidiWriteObjectRedirectedError',
    'BidiWriteObjectRequest',
    'BidiWriteObjectResponse',
    'Bucket',
    'BucketAccessControl',
    'CancelResumableWriteRequest',
    'CancelResumableWriteResponse',
    'ChecksummedData',
    'CommonObjectRequestParams',
    'ComposeObjectRequest',
    'ContentRange',
    'CreateBucketRequest',
    'CustomerEncryption',
    'DeleteBucketRequest',
    'DeleteObjectRequest',
    'GetBucketRequest',
    'GetObjectRequest',
    'ListBucketsRequest',
    'ListBucketsResponse',
    'ListObjectsRequest',
    'ListObjectsResponse',
    'LockBucketRetentionPolicyRequest',
    'MoveObjectRequest',
    'Object',
    'ObjectAccessControl',
    'ObjectChecksums',
    'ObjectContexts',
    'ObjectCustomContextPayload',
    'ObjectRangeData',
    'Owner',
    'ProjectTeam',
    'QueryWriteStatusRequest',
    'QueryWriteStatusResponse',
    'ReadObjectRequest',
    'ReadObjectResponse',
    'ReadRange',
    'ReadRangeError',
    'RestoreObjectRequest',
    'RewriteObjectRequest',
    'RewriteResponse',
    'ServiceConstants',
    'StartResumableWriteRequest',
    'StartResumableWriteResponse',
    'UpdateBucketRequest',
    'UpdateObjectRequest',
    'WriteObjectRequest',
    'WriteObjectResponse',
    'WriteObjectSpec',
)
