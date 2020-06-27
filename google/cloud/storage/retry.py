# Copyright 2020 Google LLC
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
"""Retry Strategy logic used across google.cloud.storage requests."""

# Should not be in here and only for prototyping
import six
import socket
import requests
import urllib3

from google.api_core import exceptions
from google.api_core import retry


_RETRYABLE_REASONS = frozenset(
    ["rateLimitExceeded", "backendError", "internalError", "badGateway", "serviceUnavailable"]
)


_UNSTRUCTURED_RETRYABLE_TYPES = (
    exceptions.TooManyRequests,
    exceptions.InternalServerError,
    exceptions.BadGateway,
    exceptions.ServiceUnavailable,
)


def _should_retry(exc):
    """Predicate for determining when to retry."""

    if hasattr(exc, "errors"):
        if len(exc.errors) == 0:
            # Check for unstructured error returns, e.g. from GFE
            return isinstance(exc, _UNSTRUCTURED_RETRYABLE_TYPES)
        reason = exc.errors[0]["reason"]

        return reason in _RETRYABLE_REASONS
    else:
        # Connection Reset
        if isinstance(exc, requests.exceptions.ConnectionError):
            if isinstance(exc.args[0], urllib3.exceptions.ProtocolError):
                if isinstance(exc.args[0].args[1], ConnectionResetError):
                    return True
    return False

_DEFAULT_RETRY = retry.Retry(predicate=_should_retry)
