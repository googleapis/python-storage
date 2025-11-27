# poc_bidi_retry_final.py

import asyncio
from unittest import mock
from google.api_core import exceptions
from google.api_core.retry_async import AsyncRetry

# Assuming the retry components are in these locations
# In a real scenario, these would be imported from the library
from google.cloud.storage._experimental.asyncio.retry.bidi_stream_retry_manager import (
    _BidiStreamRetryManager,
)
from google.cloud.storage._experimental.asyncio.retry.base_strategy import (
    _BaseResumptionStrategy,
)


class ReadResumptionStrategy(_BaseResumptionStrategy):
    """
    A concrete implementation of the strategy for bidi reads.
    This is a simplified version for the POC.
    """

    def __init__(self):
        self.state = {"offset": 0, "remaining_bytes": float("inf")}

    def generate_requests(self, state):
        print(f"[Strategy] Generating request with state: {state}")
        # In a real scenario, this yields ReadObjectRequest protos
        yield {"read_offset": state["offset"]}

    def handle_response(self, response):
        # In a real scenario, this is a ReadObjectResponse proto
        chunk = response.get("chunk", b"")
        self.state["offset"] += len(chunk)
        print(f"[Strategy] Handled response, new state: {self.state}")
        return response

    async def recover_state_on_failure(self, error, state):
        print(f"[Strategy] Recovering state from error: {error}. Current state: {state}")
        # For reads, the offset is already updated, so we just return the current state
        return self.state


# --- Simulation Setup ---

# A mock stream that fails once mid-stream
ATTEMPT_COUNT = 0
STREAM_CONTENT = [
    [{"chunk": b"part_one"}, {"chunk": b"part_two"}, exceptions.ServiceUnavailable("Network error")],
    [{"chunk": b"part_three"}, {"chunk": b"part_four"}],
]


async def mock_stream_opener(requests, state):
    """
    A mock stream opener that simulates a failing and then succeeding stream.
    """
    global ATTEMPT_COUNT
    print(f"\n--- Stream Attempt {ATTEMPT_COUNT + 1} ---")
    # Consume the request iterator (in a real scenario, this sends requests to gRPC)
    _ = [req for req in requests]
    print(f"Mock stream opened with state: {state}")

    content_for_this_attempt = STREAM_CONTENT[ATTEMPT_COUNT]
    ATTEMPT_COUNT += 1

    for item in content_for_this_attempt:
        await asyncio.sleep(0.01)  # Simulate network latency
        if isinstance(item, Exception):
            print(f"!!! Stream yielding an error: {item} !!!")
            raise item
        else:
            print(f"Stream yielding chunk of size: {len(item.get('chunk', b''))}")
            yield item


async def main():
    """
    Main function to run the POC.
    """
    print("--- Starting Bidi Read Retry POC ---")

    # 1. Define a retry policy
    retry_policy = AsyncRetry(
        predicate=lambda e: isinstance(e, exceptions.ServiceUnavailable),
        deadline=30.0,
        initial=0.1,  # Start with a short wait
    )

    # 2. Instantiate the strategy and retry manager
    strategy = ReadResumptionStrategy()
    retry_manager = _BidiStreamRetryManager(
        strategy=strategy, stream_opener=mock_stream_opener
    )

    # 3. Execute the operation
    print("\nExecuting the retry manager...")
    final_stream_iterator = await retry_manager.execute(
        initial_state={"offset": 0}, retry_policy=retry_policy
    )

    # 4. Consume the final, successful stream
    all_content = b""
    print("\n--- Consuming Final Stream ---")
    async for response in final_stream_iterator:
        chunk = response.get("chunk", b"")
        all_content += chunk
        print(f"Received chunk: {chunk.decode()}. Total size: {len(all_content)}")

    print("\n--- POC Finished ---")
    print(f"Final downloaded content: {all_content.decode()}")
    print(f"Total attempts made: {ATTEMPT_COUNT}")
    assert all_content == b"part_onepart_twopart_threepart_four"
    assert ATTEMPT_COUNT == 2
    print("\nAssertion passed: Content correctly assembled across retries.")


if __name__ == "__main__":
    asyncio.run(main())
