"""Helper utility for async client."""

from google.api_core import retry_async
from google.cloud.storage import retry as storage_retry
from google.cloud.storage import _helpers
from google.api_core.page_iterator_async import AsyncIterator
from google.api_core.page_iterator import Page


ASYNC_DEFAULT_RETRY = retry_async.AsyncRetry(predicate=storage_retry._should_retry)
ASYNC_DEFAULT_TIMEOUT = _helpers._DEFAULT_TIMEOUT


async def _do_nothing_page_start(iterator, page, response):
    """Async Helper to provide custom behavior after a :class:`Page` is started.

    This is a do-nothing stand-in as the default value.

    Args:
        iterator (Iterator): An iterator that holds some request info.
        page (Page): The page that was just created.
        response (Any): The API response for a page.
    """
    # pylint: disable=unused-argument
    pass

class AsyncHTTPIterator(AsyncIterator):
    """A generic class for iterating through HTTP/JSON API list responses asynchronously.

    Args:
        client (google.cloud.storage._experimental.asyncio.async_client.AsyncClient): The API client.
        api_request (Callable): The **async** function to use to make API requests.
            This must be an awaitable.
        path (str): The method path to query for the list of items.
        item_to_value (Callable[AsyncIterator, Any]): Callable to convert an item 
            from the type in the JSON response into a native object.
        items_key (str): The key in the API response where the list of items
            can be found.
        page_token (str): A token identifying a page in a result set.
        page_size (int): The maximum number of results to fetch per page.
        max_results (int): The maximum number of results to fetch.
        extra_params (dict): Extra query string parameters for the API call.
        page_start (Callable): Callable to provide special behavior after a new page 
            is created.
        next_token (str): The name of the field used in the response for page tokens.
    """

    _DEFAULT_ITEMS_KEY = "items"
    _PAGE_TOKEN = "pageToken"
    _MAX_RESULTS = "maxResults"
    _NEXT_TOKEN = "nextPageToken"
    _RESERVED_PARAMS = frozenset([_PAGE_TOKEN])

    def __init__(
        self,
        client,
        api_request,
        path,
        item_to_value,
        items_key=_DEFAULT_ITEMS_KEY,
        page_token=None,
        page_size=None,
        max_results=None,
        extra_params=None,
        page_start=_do_nothing_page_start,
        next_token=_NEXT_TOKEN,
    ):
        super().__init__(
            client, item_to_value, page_token=page_token, max_results=max_results
        )
        self.api_request = api_request
        self.path = path
        self._items_key = items_key
        self._page_size = page_size
        self._page_start = page_start
        self._next_token = next_token
        self.extra_params = extra_params.copy() if extra_params else {}
        self._verify_params()

    def _verify_params(self):
        """Verifies the parameters don't use any reserved parameter."""
        reserved_in_use = self._RESERVED_PARAMS.intersection(self.extra_params)
        if reserved_in_use:
            raise ValueError("Using a reserved parameter", reserved_in_use)

    async def _next_page(self):
        """Get the next page in the iterator asynchronously.

        Returns:
            Optional[Page]: The next page in the iterator or None if
                there are no pages left.
        """
        if self._has_next_page():
            response = await self._get_next_page_response()
            items = response.get(self._items_key, ())

            # We reuse the synchronous Page class as it is just a container
            page = Page(self, items, self.item_to_value, raw_page=response)

            await self._page_start(self, page, response)
            self.next_page_token = response.get(self._next_token)
            return page
        else:
            return None

    def _has_next_page(self):
        """Determines whether or not there are more pages with results."""
        if self.page_number == 0:
            return True

        if self.max_results is not None:
            if self.num_results >= self.max_results:
                return False

        return self.next_page_token is not None

    def _get_query_params(self):
        """Getter for query parameters for the next request."""
        result = {}
        if self.next_page_token is not None:
            result[self._PAGE_TOKEN] = self.next_page_token

        page_size = None
        if self.max_results is not None:
            page_size = self.max_results - self.num_results
            if self._page_size is not None:
                page_size = min(page_size, self._page_size)
        elif self._page_size is not None:
            page_size = self._page_size

        if page_size is not None:
            result[self._MAX_RESULTS] = page_size

        result.update(self.extra_params)
        return result

    async def _get_next_page_response(self):
        """Requests the next page from the path provided asynchronously."""
        params = self._get_query_params()
        return await self.api_request(
            method="GET", path=self.path, query_params=params
        )
