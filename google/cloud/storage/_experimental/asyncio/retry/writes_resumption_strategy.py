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

from typing import Any, Dict, IO, Iterable, Optional, Union

import google_crc32c
from google.cloud._storage_v2.types import storage as storage_type
from google.cloud._storage_v2.types.storage import BidiWriteObjectRedirectedError
from google.cloud.storage._experimental.asyncio.retry.base_strategy import (
    _BaseResumptionStrategy,
)


class _WriteState:
    """A helper class to track the state of a single upload operation.

    Attributes:
        spec (AppendObjectSpec): The specification for the object to write.
        chunk_size (int): The size of chunks to read from the buffer.
        user_buffer (IO[bytes]): The data source.
        persisted_size (int): The amount of data confirmed as persisted by the server.
        bytes_sent (int): The amount of data currently sent in the active stream.
        write_handle (bytes | BidiWriteHandle | None): The handle for the append session.
        routing_token (str | None): Token for routing to the correct backend.
        is_complete (bool): Whether the upload has finished.
    """

    def __init__(
        self,
        spec: storage_type.AppendObjectSpec,
        chunk_size: int,
        user_buffer: IO[bytes],
    ):
        self.spec = spec
        self.chunk_size = chunk_size
        self.user_buffer = user_buffer
        self.persisted_size: int = 0
        self.bytes_sent: int = 0
        self.write_handle: Union[bytes, storage_type.BidiWriteHandle, None] = None
        self.routing_token: Optional[str] = None
        self.is_complete: bool = False


class _WriteResumptionStrategy(_BaseResumptionStrategy):
    """The concrete resumption strategy for bidi writes."""

    def generate_requests(
        self, state: Dict[str, Any]
    ) -> Iterable[storage_type.BidiWriteObjectRequest]:
        """Generates BidiWriteObjectRequests to resume or continue the upload.

        For Appendable Objects, every stream opening should send an
        AppendObjectSpec. If resuming, the `write_handle` is added to that spec.
        """
        write_state: _WriteState = state["write_state"]

        if write_state.write_handle:
            write_state.spec.write_handle = write_state.write_handle

        if write_state.routing_token:
            write_state.spec.routing_token = write_state.routing_token

        do_state_lookup = write_state.write_handle is not None
        yield storage_type.BidiWriteObjectRequest(
            append_object_spec=write_state.spec, state_lookup=do_state_lookup
        )

        # The buffer should already be seeked to the correct position (persisted_size)
        # by the `recover_state_on_failure` method before this is called.
        while not write_state.is_complete:
            chunk = write_state.user_buffer.read(write_state.chunk_size)

            # End of File detection
            if not chunk:
                write_state.is_complete = True
                yield storage_type.BidiWriteObjectRequest(
                    write_offset=write_state.bytes_sent,
                    finish_write=True,
                )
                return

            checksummed_data = storage_type.ChecksummedData(content=chunk)
            checksum = google_crc32c.Checksum(chunk)
            checksummed_data.crc32c = int.from_bytes(checksum.digest(), "big")

            request = storage_type.BidiWriteObjectRequest(
                write_offset=write_state.bytes_sent,
                checksummed_data=checksummed_data,
            )
            write_state.bytes_sent += len(chunk)

            yield request

    def update_state_from_response(
        self, response: storage_type.BidiWriteObjectResponse, state: Dict[str, Any]
    ) -> None:
        """Processes a server response and updates the write state."""
        write_state: _WriteState = state["write_state"]

        if response.persisted_size is not None:
            if response.persisted_size > write_state.persisted_size:
                write_state.persisted_size = response.persisted_size

        if response.write_handle:
            write_state.write_handle = response.write_handle

        if response.resource:
            write_state.is_complete = True
            write_state.persisted_size = response.resource.size

    async def recover_state_on_failure(
        self, error: Exception, state: Dict[str, Any]
    ) -> None:
        """Handles errors, specifically BidiWriteObjectRedirectedError, and rewinds state."""
        write_state: _WriteState = state["write_state"]
        cause = getattr(error, "cause", error)

        # Extract routing token and potentially a new write handle.
        if isinstance(cause, BidiWriteObjectRedirectedError):
            if cause.routing_token:
                write_state.routing_token = cause.routing_token

            if hasattr(cause, "write_handle") and cause.write_handle:
                write_state.write_handle = cause.write_handle

        # We must assume any data sent beyond 'persisted_size' was lost.
        # Reset the user buffer to the last known good byte.
        write_state.user_buffer.seek(write_state.persisted_size)
        write_state.bytes_sent = write_state.persisted_size
