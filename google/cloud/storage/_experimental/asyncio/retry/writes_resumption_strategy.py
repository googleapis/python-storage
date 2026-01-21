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

from typing import Any, Dict, IO, List, Optional, Union

import google_crc32c
from google.cloud._storage_v2.types import storage as storage_type
from google.cloud._storage_v2.types.storage import BidiWriteObjectRedirectedError
from google.cloud.storage._experimental.asyncio.retry.base_strategy import (
    _BaseResumptionStrategy,
)
from google.cloud.storage._experimental.asyncio.retry._helpers import (
    _extract_bidi_writes_redirect_proto,
)


_BIDI_WRITE_REDIRECTED_TYPE_URL = (
    "type.googleapis.com/google.storage.v2.BidiWriteObjectRedirectedError"
)


class _WriteState:
    """A helper class to track the state of a single upload operation.

    :type chunk_size: int
    :param chunk_size: The size of chunks to write to the server.

    :type user_buffer: IO[bytes]
    :param user_buffer: The data source.

    :type flush_interval: Optional[int]
    :param flush_interval: The flush interval at which the data is flushed.
    """

    def __init__(
        self,
        chunk_size: int,
        user_buffer: IO[bytes],
        flush_interval: Optional[int] = None,
    ):
        print(
            f"Initializing _WriteState with chunk_size: {chunk_size}, flush_interval: {flush_interval}"
        )
        self.chunk_size = chunk_size
        self.user_buffer = user_buffer
        self.persisted_size: int = 0
        self.bytes_sent: int = 0
        self.bytes_since_last_flush: int = 0
        self.flush_interval: Optional[int] = flush_interval
        self.write_handle: Union[bytes, storage_type.BidiWriteHandle, None] = None
        self.routing_token: Optional[str] = None
        self.is_finalized: bool = False

    def __str__(self):
        return (
            f"<_WriteState: chunk_size={self.chunk_size}, "
            f"persisted_size={self.persisted_size}, bytes_sent={self.bytes_sent}, "
            f"bytes_since_last_flush={self.bytes_since_last_flush}, "
            f"flush_interval={self.flush_interval}, write_handle={self.write_handle}, "
            f"routing_token={self.routing_token}, is_finalized={self.is_finalized}>"
        )


class _WriteResumptionStrategy(_BaseResumptionStrategy):
    """The concrete resumption strategy for bidi writes."""

    def generate_requests(self, state: Dict[str, Any]):
        """Generates BidiWriteObjectRequests to resume or continue the upload.

        This method is a generator that yields requests one at a time,
        allowing for incremental sending and better memory efficiency.

        On retry/redirect, yields a state_lookup request first to get the current
        persisted state from the server before sending data requests.

        The last data request is always yielded with state_lookup=True and flush=True
        to ensure the server persists the final data and returns the updated state.
        """
        write_state: _WriteState = state["write_state"]
        print(f"Generating requests with state: {write_state}")

        # If this is a retry/redirect, yield a state lookup request first
        # This allows the sender to get current persisted_size before proceeding
        if (
            write_state.routing_token
            or write_state.bytes_sent > write_state.persisted_size
        ):
            # Yield an open/state-lookup request with no data
            print("Yielding state_lookup request.")
            yield storage_type.BidiWriteObjectRequest(state_lookup=True)

        # The buffer should already be seeked to the correct position (persisted_size)
        # by the `recover_state_on_failure` method before this is called.
        while not write_state.is_finalized:
            chunk = write_state.user_buffer.read(write_state.chunk_size)
            print(f"Read chunk of size: {len(chunk)}")

            if not chunk:
                break

            # Peek to see if this is the last chunk. This is safe because both
            # io.BytesIO and BufferedReader (used in file uploads) support peek().
            is_last_chunk = not getattr(write_state.user_buffer, "peek", lambda n: b"")(
                1
            )

            checksummed_data = storage_type.ChecksummedData(content=chunk)
            checksum = google_crc32c.Checksum(chunk)
            checksummed_data.crc32c = int.from_bytes(checksum.digest(), "big")

            request = storage_type.BidiWriteObjectRequest(
                write_offset=write_state.bytes_sent,
                checksummed_data=checksummed_data,
            )
            chunk_len = len(chunk)
            write_state.bytes_sent += chunk_len
            write_state.bytes_since_last_flush += chunk_len
            print(f"Yielding request with offset: {request.write_offset}")

            if (
                write_state.flush_interval
                and write_state.bytes_since_last_flush >= write_state.flush_interval
            ):
                request.flush = True
                print("Marking request with flush=True")
                # reset counter after marking flush
                write_state.bytes_since_last_flush = 0

            if is_last_chunk:
                request.flush = True
                request.state_lookup = True
                print("Marking request with flush=True and state_lookup=True")

            yield request

    def update_state_from_response(
        self, response: storage_type.BidiWriteObjectResponse, state: Dict[str, Any]
    ) -> None:
        """Processes a server response and updates the write state."""
        write_state: _WriteState = state["write_state"]
        print(f"Updating state from response: {response}")
        if response is None:
            return
        if response.persisted_size:
            write_state.persisted_size = response.persisted_size

        if response.write_handle:
            write_state.write_handle = response.write_handle

        if response.resource:
            write_state.persisted_size = response.resource.size
            if response.resource.finalize_time:
                write_state.is_finalized = True
        print(f"New state: {write_state}")

    async def recover_state_on_failure(
        self, error: Exception, state: Dict[str, Any]
    ) -> None:
        """
        Handles errors, specifically BidiWriteObjectRedirectedError, and rewinds state.

        This method rewinds the user buffer and internal byte tracking to the
        last confirmed 'persisted_size' from the server.
        """
        print(f"Recovering from error: {error}")
        write_state: _WriteState = state["write_state"]

        redirect_proto = None

        if isinstance(error, BidiWriteObjectRedirectedError):
            redirect_proto = error
        else:
            redirect_proto = _extract_bidi_writes_redirect_proto(error)

        # Extract routing token and potentially a new write handle for redirection.
        if redirect_proto:
            if redirect_proto.routing_token:
                write_state.routing_token = redirect_proto.routing_token
            if redirect_proto.write_handle:
                write_state.write_handle = redirect_proto.write_handle

        # We must assume any data sent beyond 'persisted_size' was lost.
        # Reset the user buffer to the last known good byte confirmed by the server.
        print(f"Seeking buffer to: {write_state.persisted_size}")
        write_state.user_buffer.seek(write_state.persisted_size)
        write_state.bytes_sent = write_state.persisted_size
        write_state.bytes_since_last_flush = 0
        print(f"Recovered state: {write_state}")

