import asyncio
from typing import Any, AsyncIterator, Callable

from google.api_core import exceptions
from google.cloud.storage._experimental.asyncio.retry.base_strategy import (
    _BaseResumptionStrategy,
)


class _BidiStreamRetryManager:
    """Manages the generic retry loop for a bidi streaming operation."""

    def __init__(
        self,
        strategy: _BaseResumptionStrategy,
        stream_opener: Callable[..., AsyncIterator[Any]],
        retry_policy,
    ):
        """Initializes the retry manager."""
        self._strategy = strategy
        self._stream_opener = stream_opener
        self._retry_policy = retry_policy

    async def execute(self, initial_state: Any):
        """
        Executes the bidi operation with the configured retry policy.

        This method implements a manual retry loop that provides the necessary
        control points to manage state between attempts, which is not possible
        with a simple retry decorator.
        """
        state = initial_state
        retry_policy = self._retry_policy

        while True:
            try:
                # 1. Generate requests based on the current state.
                requests = self._strategy.generate_requests(state)

                # 2. Open and consume the stream.
                stream = self._stream_opener(requests, state)
                async for response in stream:
                    self._strategy.update_state_from_response(response, state)

                # 3. If the stream completes without error, exit the loop.
                return

            except Exception as e:
                # 4. If an error occurs, check if it's retriable.
                if not retry_policy.predicate(e):
                    # If not retriable, fail fast.
                    raise

                # 5. If retriable, allow the strategy to recover state.
                #    This is where routing tokens are extracted or QueryWriteStatus is called.
                try:
                    await self._strategy.recover_state_on_failure(e, state)
                except Exception as recovery_exc:
                    # If state recovery itself fails, we must abort.
                    raise exceptions.RetryError(
                        "Failed to recover state after a transient error.",
                        cause=recovery_exc,
                    ) from recovery_exc

                # 6. Use the policy to sleep and check for deadline expiration.
                #    This will raise a RetryError if the deadline is exceeded.
                await asyncio.sleep(await retry_policy.sleep(e))
