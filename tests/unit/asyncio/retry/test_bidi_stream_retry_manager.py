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
import unittest
from unittest import mock

import pytest
from google.api_core import exceptions
from google.api_core.retry_async import AsyncRetry

from google.cloud.storage._experimental.asyncio.retry import bidi_stream_retry_manager as manager
from google.cloud.storage._experimental.asyncio.retry import base_strategy


def _is_retriable(exc):
    return isinstance(exc, exceptions.ServiceUnavailable)

DEFAULT_TEST_RETRY = AsyncRetry(predicate=_is_retriable, deadline=1)


class TestBidiStreamRetryManager(unittest.IsolatedAsyncioTestCase):
    async def test_execute_success_on_first_try(self):
        mock_strategy = mock.AsyncMock(spec=base_strategy._BaseResumptionStrategy)
        async def mock_stream_opener(*args, **kwargs):
            yield "response_1"

        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy, stream_opener=mock_stream_opener
        )
        await retry_manager.execute(initial_state={}, retry_policy=DEFAULT_TEST_RETRY)
        mock_strategy.generate_requests.assert_called_once()
        mock_strategy.update_state_from_response.assert_called_once_with("response_1", {})
        mock_strategy.recover_state_on_failure.assert_not_called()

    async def test_execute_retries_and_succeeds(self):
        mock_strategy = mock.AsyncMock(spec=base_strategy._BaseResumptionStrategy)
        attempt_count = 0
        async def mock_stream_opener(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise exceptions.ServiceUnavailable("Service is down")
            else:
                yield "response_2"

        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy, stream_opener=mock_stream_opener
        )
        retry_policy = AsyncRetry(predicate=_is_retriable, initial=0.01)
        await retry_manager.execute(initial_state={}, retry_policy=retry_policy)

        self.assertEqual(attempt_count, 2)
        self.assertEqual(mock_strategy.generate_requests.call_count, 2)
        mock_strategy.recover_state_on_failure.assert_called_once()
        mock_strategy.update_state_from_response.assert_called_once_with("response_2", {})

    async def test_execute_fails_after_deadline_exceeded(self):
        mock_strategy = mock.AsyncMock(spec=base_strategy._BaseResumptionStrategy)
        async def mock_stream_opener(*args, **kwargs):
            if False:
                yield
            raise exceptions.ServiceUnavailable("Service is always down")

        fast_retry = AsyncRetry(predicate=_is_retriable, deadline=0.01, initial=0.02)
        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy, stream_opener=mock_stream_opener
        )
        with pytest.raises(exceptions.RetryError, match="Deadline of 0.01s exceeded"):
            await retry_manager.execute(initial_state={}, retry_policy=fast_retry)

        self.assertGreater(mock_strategy.recover_state_on_failure.call_count, 0)

    async def test_execute_fails_immediately_on_non_retriable_error(self):
        mock_strategy = mock.AsyncMock(spec=base_strategy._BaseResumptionStrategy)
        async def mock_stream_opener(*args, **kwargs):
            if False:
                yield
            raise exceptions.PermissionDenied("Auth error")

        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy, stream_opener=mock_stream_opener
        )
        with pytest.raises(exceptions.PermissionDenied):
            await retry_manager.execute(initial_state={}, retry_policy=DEFAULT_TEST_RETRY)

        mock_strategy.recover_state_on_failure.assert_not_called()
