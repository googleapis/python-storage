# Copyright 2024 Google LLC
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

"""User-defined object contexts for Google Cloud Storage."""

from typing import Dict, Any, Optional
import datetime

from google.cloud._helpers import _rfc3339_nanos_to_datetime
from google.cloud._helpers import _datetime_to_rfc3339

_VALUE = "value"
_CREATE_TIME = "createTime"
_UPDATE_TIME = "updateTime"
_CUSTOM = "custom"


class ObjectCustomContextPayload:
    """The payload of a single user-defined object context.

    :type value: str
    :param value: The value of the object context.

    :type create_time: :class:`datetime.datetime` or ``NoneType``
    :param create_time: (Optional) The time at which the object context was created.

    :type update_time: :class:`datetime.datetime` or ``NoneType``
    :param update_time: (Optional) The time at which the object context was last updated.
    """

    def __init__(
        self,
        value: str,
        create_time: Optional[datetime.datetime] = None,
        update_time: Optional[datetime.datetime] = None,
    ):
        self.value = value
        self.create_time = create_time
        self.update_time = update_time

    @classmethod
    def _from_api_resource(cls, resource: Dict[str, Any]) -> "ObjectCustomContextPayload":
        """Factory: creates an ObjectCustomContextPayload instance from a server response."""
        create_time = resource.get(_CREATE_TIME)
        if create_time:
            create_time = _rfc3339_nanos_to_datetime(create_time)

        update_time = resource.get(_UPDATE_TIME)
        if update_time:
            update_time = _rfc3339_nanos_to_datetime(update_time)

        return cls(
            value=resource.get(_VALUE),
            create_time=create_time,
            update_time=update_time,
        )

    def _to_api_resource(self) -> Dict[str, Any]:
        """Serializes this object to a dictionary for API requests."""
        resource = {_VALUE: self.value}
        if self.create_time:
            resource[_CREATE_TIME] = _datetime_to_rfc3339(self.create_time)
        if self.update_time:
            resource[_UPDATE_TIME] = _datetime_to_rfc3339(self.update_time)
        return resource


class ObjectContexts:
    """User-defined object contexts.

    This class is a helper for constructing the contexts dictionary to be
    assigned to a blob's ``contexts`` property.

    :type custom: dict or ``NoneType``
    :param custom:
        (Optional) User-defined object contexts, a dictionary mapping string keys
        to :class:`ObjectCustomContextPayload` instances. To delete a context via
        patch, the payload can be mapped to ``None``.
    """

    def __init__(
        self,
        custom: Optional[Dict[str, Optional[ObjectCustomContextPayload]]] = None,
    ):
        self.custom = custom or {}

    @classmethod
    def _from_api_resource(cls, resource: Dict[str, Any]) -> "ObjectContexts":
        """Factory: creates an ObjectContexts instance from a server response."""
        custom_data = resource.get(_CUSTOM)
        custom = {}
        if custom_data:
            for key, payload in custom_data.items():
                if payload is not None:
                    custom[key] = ObjectCustomContextPayload._from_api_resource(payload)
                else:
                    custom[key] = None

        return cls(custom=custom)

    def _to_api_resource(self) -> Dict[str, Any]:
        """Serializes this object to a dictionary for API requests."""
        resource = {}
        if self.custom is not None:
            custom_resource = {}
            for key, payload in self.custom.items():
                if payload is None:
                    custom_resource[key] = None
                elif isinstance(payload, ObjectCustomContextPayload):
                    custom_resource[key] = payload._to_api_resource()
                else:
                    custom_resource[key] = payload
            resource[_CUSTOM] = custom_resource
        return resource
