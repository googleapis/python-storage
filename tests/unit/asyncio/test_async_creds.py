import unittest.mock
import pytest
from google.auth import credentials as google_creds
from google.auth.transport.requests import Request
from google.cloud.storage._experimental.asyncio.async_creds import AsyncCredsWrapper


@pytest.fixture
def mock_sync_creds():
    """Creates a mock of the synchronous Google Credentials object."""
    creds = unittest.mock.create_autospec(google_creds.Credentials, instance=True)
    type(creds).valid = unittest.mock.PropertyMock(return_value=True)
    return creds

@pytest.fixture
def async_wrapper(mock_sync_creds):
    """Instantiates the wrapper with the mock credentials."""
    return AsyncCredsWrapper(mock_sync_creds)


class TestAsyncCredsWrapper:
    
    @pytest.mark.asyncio
    async def test_init_sets_attributes(self, async_wrapper, mock_sync_creds):
        """Test that the wrapper initializes correctly."""
        assert async_wrapper.creds == mock_sync_creds

    @pytest.mark.asyncio
    async def test_valid_property_delegates(self, async_wrapper, mock_sync_creds):
        """Test that the .valid property maps to the sync creds .valid property."""
        type(mock_sync_creds).valid = unittest.mock.PropertyMock(return_value=True)
        assert async_wrapper.valid is True
        
        type(mock_sync_creds).valid = unittest.mock.PropertyMock(return_value=False)
        assert async_wrapper.valid is False

    @pytest.mark.asyncio
    async def test_refresh_offloads_to_executor(self, async_wrapper, mock_sync_creds):
        """Test that refresh() gets the running loop and calls sync refresh in executor."""        
        with unittest.mock.patch('asyncio.get_running_loop') as mock_get_loop:
            mock_loop = unittest.mock.AsyncMock()
            mock_get_loop.return_value = mock_loop
            
            await async_wrapper.refresh(None)
            
            mock_loop.run_in_executor.assert_called_once()
            
            args, _ = mock_loop.run_in_executor.call_args
            assert args[1] == mock_sync_creds.refresh
            assert isinstance(args[2], Request)

    @pytest.mark.asyncio
    async def test_before_request_valid_creds(self, async_wrapper, mock_sync_creds):
        """Test before_request when credentials are ALREADY valid (fast path)."""
        type(mock_sync_creds).valid = unittest.mock.PropertyMock(return_value=True)
        
        headers = {}
        await async_wrapper.before_request(None, "GET", "http://example.com", headers)
        
        # Should call apply() directly on sync creds
        mock_sync_creds.apply.assert_called_once_with(headers)
        
        # Should NOT call before_request on sync creds
        mock_sync_creds.before_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_before_request_invalid_creds(self, async_wrapper, mock_sync_creds):
        """Test before_request when credentials are INVALID (refresh path)."""
        type(mock_sync_creds).valid = unittest.mock.PropertyMock(return_value=False)
        
        headers = {}
        method = "GET"
        url = "http://example.com"

        with unittest.mock.patch('asyncio.get_running_loop') as mock_get_loop:
            mock_loop = unittest.mock.AsyncMock()
            mock_get_loop.return_value = mock_loop

            await async_wrapper.before_request(None, method, url, headers)

            mock_loop.run_in_executor.assert_called_once()
            
            args, _ = mock_loop.run_in_executor.call_args
            assert args[1] == mock_sync_creds.before_request
            assert isinstance(args[2], Request)
            assert args[3] == method
            assert args[4] == url
            assert args[5] == headers