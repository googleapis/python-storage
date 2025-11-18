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

import asyncio
import time
from typing import Any, AsyncIterator, Callable

from google.api_core import exceptions
from google.api_core.retry.retry_base import exponential_sleep_generator
from google.cloud.storage._experimental.asyncio.retry.base_strategy import (
    _BaseResumptionStrategy,
)


class _BidiStreamRetryManager:
    """Manages the generic retry loop for a bidi streaming operation."""

    def __init__(
        self,
        strategy: _BaseResumptionStrategy,
        stream_opener: Callable[..., AsyncIterator[Any]],
    ):
        """Initializes the retry manager.

        Args:
            strategy: The strategy for managing the state of a specific
                bidi operation (e.g., reads or writes).
            stream_opener: An async callable that opens a new gRPC stream.
        """
        self._strategy = strategy
        self._stream_opener = stream_opener

    async def execute(self, initial_state: Any, retry_policy):
        """
        Executes the bidi operation with the configured retry policy.

        This method implements a manual retry loop that provides the necessary
        control points to manage state between attempts.

        Args:
            initial_state: An object containing all state for the operation.
            retry_policy: The `google.api_core.retry.AsyncRetry` object to
                govern the retry behavior for this specific operation.
        """
        state = initial_state

        deadline = time.monotonic() + retry_policy._deadline if retry_policy._deadline else 0

        sleep_generator = exponential_sleep_generator(
            retry_policy._initial, retry_policy._maximum, retry_policy._multiplier
        )

        while True:
            try:
                requests = self._strategy.generate_requests(state)
                stream = self._stream_opener(requests, state)
                async for response in stream:
                    self._strategy.update_state_from_response(response, state)
                return
            except Exception as e:
                # AsyncRetry may expose either 'on_error' (public) or the private
                # '_on_error' depending on google.api_core version. Call whichever
                # exists so the retry policy can decide to raise (non-retriable /
                # deadline exceeded) or allow a retry.
                on_error_callable = getattr(retry_policy, "on_error", None)
                if on_error_callable is None:
                    on_error_callable = getattr(retry_policy, "_on_error", None)

                if on_error_callable is None:
                    # No hook available on the policy; re-raise the error.
                    raise

                # Let the retry policy handle the error (may raise RetryError).
                await on_error_callable(e)

                # If the retry policy did not raise, allow the strategy to recover
                # and then sleep per policy before next attempt.
                await self._strategy.recover_state_on_failure(e, state)
                await retry_policy.sleep()
