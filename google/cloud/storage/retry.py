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

import requests

from google.api_core import exceptions
from google.api_core import retry

import json


_RETRYABLE_TYPES = (
    exceptions.TooManyRequests,  # 429
    exceptions.InternalServerError,  # 500
    exceptions.BadGateway,  # 502
    exceptions.ServiceUnavailable,  # 503
    exceptions.GatewayTimeout,  # 504
    requests.ConnectionError,
)


def _should_retry(exc):
    """Predicate for determining when to retry."""
    return isinstance(exc, _RETRYABLE_TYPES)


DEFAULT_RETRY = retry.Retry(predicate=_should_retry)
"""The default retry object.

To modify the default retry behavior, call a ``with_XXX`` method
on ``DEFAULT_RETRY``. For example, to change the deadline to 30 seconds,
pass ``retry=DEFAULT_RETRY.with_deadline(30)``. See google-api-core reference
(https://googleapis.dev/python/google-api-core/latest/retry.html) for details.
"""


class ConditionalRetryPolicy(object):
    def __init__(self, retry_policy, conditional_predicate, required_kwargs):
        self.retry_policy = retry_policy
        self.conditional_predicate = conditional_predicate
        self.required_kwargs = required_kwargs

    def get_retry_policy_if_conditions_met(self, **kwargs):
        if self.conditional_predicate(*[kwargs[key] for key in self.required_kwargs]):
            return self.retry_policy
        return None


def is_generation_specified(query_params):
    """Return True if generation or if_generation_match is specified."""
    generation = query_params.get("generation") is not None
    if_generation_match = query_params.get("if_generation_match") is not None
    return generation or if_generation_match


def is_metageneration_specified(query_params):
    """Return True if if_metageneration_match is specified."""
    if_metageneration_match = query_params.get("if_metageneration_match") is not None
    return if_metageneration_match


def is_etag_in_json(query_params, data):
    """Return True if an etag is contained in the JSON body.

    Indended for use on calls with relatively short JSON payloads."""
    try:
        content = json.loads(data)
        if content.get("etag"):
            return True
    except (json.decoder.JSONDecodeError, TypeError):
        pass
    return False


DEFAULT_RETRY_IF_GENERATION_SPECIFIED = ConditionalRetryPolicy(
    DEFAULT_RETRY, is_generation_specified, ["query_params"]
)
DEFAULT_RETRY_IF_METAGENERATION_SPECIFIED = ConditionalRetryPolicy(
    DEFAULT_RETRY, is_metageneration_specified, ["query_params"]
)
DEFAULT_RETRY_IF_ETAG_IN_JSON = ConditionalRetryPolicy(
    DEFAULT_RETRY, is_etag_in_json, ["query_params", "data"]
)
