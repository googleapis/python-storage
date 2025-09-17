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
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from google.cloud.storage._experimental.asyncio.async_abstract_object_stream import (
    _AsyncAbstractObjectStream,
)


# A concrete implementation for testing purposes.
class _ConcreteStream(_AsyncAbstractObjectStream):
    async def open(self):
        pass

    async def close(self):
        pass

    async def send(self):
        pass

    async def recv(self):
        pass


def test_init():
    """Test the constructor of AsyncAbstractObjectStream."""
    bucket_name = "test-bucket"
    object_name = "test-object"
    generation = 12345

    # Test with all parameters
    stream = _ConcreteStream(bucket_name, object_name, generation_number=generation)
    assert stream.bucket_name == bucket_name
    assert stream.object_name == object_name
    assert stream.generation_number == generation

    # Test with default generation_number
    stream_no_gen = _ConcreteStream(bucket_name, object_name)
    assert stream_no_gen.bucket_name == bucket_name
    assert stream_no_gen.object_name == object_name
    assert stream_no_gen.generation_number is None


def test_instantiation_fails_without_implementation():
    """Test that instantiating an incomplete subclass raises TypeError."""

    class _IncompleteStream(_AsyncAbstractObjectStream):
        # Missing implementations for abstract methods like open(), close(), etc.
        pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        _IncompleteStream("bucket", "object")
