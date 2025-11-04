import unittest
from unittest import mock

import pytest
from google.api_core import exceptions
from google.api_core.retry.retry_streaming_async import AsyncStreamingRetry

from google.cloud.storage._experimental.asyncio.retry import manager
from google.cloud.storage._experimental.asyncio.retry import strategy


def _is_retriable(exc):
    return isinstance(exc, exceptions.ServiceUnavailable)


DEFAULT_TEST_RETRY = AsyncStreamingRetry(predicate=_is_retriable, deadline=1)


class TestBidiStreamRetryManager(unittest.IsolatedAsyncioTestCase):
    async def test_execute_success_on_first_try(self):
        """Verify the manager correctly handles a stream that succeeds immediately."""
        mock_strategy = mock.AsyncMock(spec=strategy._BaseResumptionStrategy)

        async def mock_stream_opener(*args, **kwargs):
            yield "response_1"

        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy,
            stream_opener=mock_stream_opener,
            retry_policy=DEFAULT_TEST_RETRY,
        )

        await retry_manager.execute(initial_state={})

        mock_strategy.generate_requests.assert_called_once()
        mock_strategy.update_state_from_response.assert_called_once_with(
            "response_1", {}
        )
        mock_strategy.recover_state_on_failure.assert_not_called()

    async def test_execute_retries_and_succeeds(self):
        """Verify the manager retries on a transient error and then succeeds."""
        mock_strategy = mock.AsyncMock(spec=strategy._BaseResumptionStrategy)

        attempt_count = 0

        async def mock_stream_opener(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise exceptions.ServiceUnavailable("Service is down")
            else:
                yield "response_2"

        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy,
            stream_opener=mock_stream_opener,
            retry_policy=AsyncStreamingRetry(predicate=_is_retriable, initial=0.01),
        )

        await retry_manager.execute(initial_state={})

        self.assertEqual(attempt_count, 2)
        self.assertEqual(mock_strategy.generate_requests.call_count, 2)
        mock_strategy.recover_state_on_failure.assert_called_once()
        mock_strategy.update_state_from_response.assert_called_once_with(
            "response_2", {}
        )

    async def test_execute_fails_after_deadline_exceeded(self):
        """Verify the manager raises RetryError if the deadline is exceeded."""
        mock_strategy = mock.AsyncMock(spec=strategy._BaseResumptionStrategy)

        async def mock_stream_opener(*args, **kwargs):
            raise exceptions.ServiceUnavailable("Service is always down")

        # Use a very short deadline to make the test fast.
        fast_retry = AsyncStreamingRetry(
            predicate=_is_retriable, deadline=0.1, initial=0.05
        )
        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy,
            stream_opener=mock_stream_opener,
            retry_policy=fast_retry,
        )

        with pytest.raises(exceptions.RetryError, match="Deadline of 0.1s exceeded"):
            await retry_manager.execute(initial_state={})

        # Verify it attempted to recover state after each failure.
        self.assertGreater(mock_strategy.recover_state_on_failure.call_count, 1)

    async def test_execute_fails_immediately_on_non_retriable_error(self):
        """Verify the manager aborts immediately on a non-retriable error."""
        mock_strategy = mock.AsyncMock(spec=strategy._BaseResumptionStrategy)

        async def mock_stream_opener(*args, **kwargs):
            raise exceptions.PermissionDenied("Auth error")

        retry_manager = manager._BidiStreamRetryManager(
            strategy=mock_strategy,
            stream_opener=mock_stream_opener,
            retry_policy=DEFAULT_TEST_RETRY,
        )

        with pytest.raises(exceptions.PermissionDenied):
            await retry_manager.execute(initial_state={})

        # Verify that it did not try to recover or update state.
        mock_strategy.recover_state_on_failure.assert_not_called()
        mock_strategy.update_state_from_response.assert_not_called()
