# Copyright 2026 Google LLC
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

import mock
import pytest
from google.api_core.page_iterator import Page
from google.cloud.storage._experimental.asyncio.async_helpers import AsyncHTTPIterator


async def _safe_anext(iterator):
    """Helper to get the next item or return None (Py3.9 compatible)."""
    try:
        return await iterator.__anext__()
    except StopAsyncIteration:
        return None


class TestAsyncHTTPIterator:
    def _make_one(self, *args, **kw):
        return AsyncHTTPIterator(*args, **kw)

    @pytest.mark.asyncio
    async def test_iterate_items_single_page(self):
        """Test simple iteration over one page of results."""
        client = mock.Mock()
        api_request = mock.AsyncMock()
        api_request.return_value = {"items": ["a", "b"]}

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=lambda _, x: x.upper(),
        )

        results = []
        async for item in iterator:
            results.append(item)

        assert results == ["A", "B"]
        assert iterator.num_results == 2
        assert iterator.page_number == 1
        api_request.assert_awaited_once_with(
            method="GET", path="/path", query_params={}
        )

    @pytest.mark.asyncio
    async def test_iterate_items_multiple_pages(self):
        """Test pagination flow passes tokens correctly."""
        client = mock.Mock()
        api_request = mock.AsyncMock()

        # Setup Response: 2 Pages
        api_request.side_effect = [
            {"items": ["1", "2"], "nextPageToken": "token-A"},  # Page 1
            {"items": ["3"], "nextPageToken": "token-B"},  # Page 2
            {"items": []},  # Page 3 (Empty/End)
        ]

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=lambda _, x: int(x),
        )

        results = [i async for i in iterator]

        assert results == [1, 2, 3]
        assert api_request.call_count == 3

        calls = api_request.call_args_list
        assert calls[0].kwargs["query_params"] == {}
        assert calls[1].kwargs["query_params"] == {"pageToken": "token-A"}
        assert calls[2].kwargs["query_params"] == {"pageToken": "token-B"}

    @pytest.mark.asyncio
    async def test_iterate_pages_public_property(self):
        """Test the .pages property which yields Page objects instead of items."""
        client = mock.Mock()
        api_request = mock.AsyncMock()

        api_request.side_effect = [
            {"items": ["a"], "nextPageToken": "next"},
            {"items": ["b"]},
        ]

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=lambda _, x: x,
        )

        pages = []
        async for page in iterator.pages:
            pages.append(page)
            assert isinstance(page, Page)

        assert len(pages) == 2
        assert list(pages[0]) == ["a"]
        assert list(pages[1]) == ["b"]
        assert iterator.page_number == 2

    @pytest.mark.asyncio
    async def test_max_results_limits_requests(self):
        """Test that max_results alters the request parameters dynamically."""
        client = mock.Mock()
        api_request = mock.AsyncMock()

        # Setup: We want 5 items total.
        # Page 1 returns 3 items.
        # Page 2 *should* only be asked for 2 items.
        api_request.side_effect = [
            {"items": ["a", "b", "c"], "nextPageToken": "t1"},
            {"items": ["d", "e"], "nextPageToken": "t2"},
        ]

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=lambda _, x: x,
            max_results=5,  # <--- Limit set here
        )

        results = [i async for i in iterator]

        assert len(results) == 5
        assert results == ["a", "b", "c", "d", "e"]

        # Verify Request 1: Asked for max 5
        call1_params = api_request.call_args_list[0].kwargs["query_params"]
        assert call1_params["maxResults"] == 5

        # Verify Request 2: Asked for max 2 (5 - 3 already fetched)
        call2_params = api_request.call_args_list[1].kwargs["query_params"]
        assert call2_params["maxResults"] == 2
        assert call2_params["pageToken"] == "t1"

    @pytest.mark.asyncio
    async def test_extra_params_passthrough(self):
        """Test that extra_params are merged into every request."""
        client = mock.Mock()
        api_request = mock.AsyncMock(return_value={"items": []})

        custom_params = {"projection": "full", "delimiter": "/"}

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=mock.Mock(),
            extra_params=custom_params,  # <--- Input
        )

        # Trigger a request
        await _safe_anext(iterator)

        # Verify Request Pattern
        call_params = api_request.call_args.kwargs["query_params"]
        assert call_params["projection"] == "full"
        assert call_params["delimiter"] == "/"

    @pytest.mark.asyncio
    async def test_page_size_configuration(self):
        """Test that page_size is sent as maxResults if no global max_results is set."""
        client = mock.Mock()
        api_request = mock.AsyncMock(return_value={"items": []})

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=mock.Mock(),
            page_size=50,  # <--- User preference
        )

        await _safe_anext(iterator)

        # Verify Request Pattern
        call_params = api_request.call_args.kwargs["query_params"]
        assert call_params["maxResults"] == 50

    @pytest.mark.asyncio
    async def test_page_start_callback(self):
        """Verify the page_start callback is invoked during iteration."""
        client = mock.Mock()
        api_request = mock.AsyncMock(return_value={"items": ["x"]})
        callback = mock.AsyncMock()

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=lambda _, x: x,
            page_start=callback,
        )

        # Run iteration
        async for _ in iterator:
            pass

        # Verify callback was awaited
        callback.assert_awaited_once()
        args = callback.call_args[0]
        assert args[0] is iterator
        assert isinstance(args[1], Page)
        assert args[2] == {"items": ["x"]}

    @pytest.mark.asyncio
    async def test_iterate_empty_response(self):
        """Test iteration over an empty result set."""
        client = mock.Mock()
        api_request = mock.AsyncMock(return_value={"items": []})

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=mock.Mock(),
        )

        results = [i async for i in iterator]
        assert results == []
        assert iterator.num_results == 0
        assert iterator.page_number == 1

    @pytest.mark.asyncio
    async def test_error_if_iterated_twice(self):
        """Verify the iterator cannot be restarted once started."""
        client = mock.Mock()
        api_request = mock.AsyncMock(return_value={"items": []})

        iterator = self._make_one(
            client=client,
            api_request=api_request,
            path="/path",
            item_to_value=mock.Mock(),
        )

        # First Start
        async for _ in iterator:
            pass

        # Second Start (Should Fail)
        with pytest.raises(ValueError, match="Iterator has already started"):
            async for _ in iterator:
                pass
