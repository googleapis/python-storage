import sys
import unittest.mock
import pytest
from google.auth import credentials as google_creds
from google.cloud.storage._experimental.asyncio import async_creds


@pytest.fixture
def mock_aio_modules():
    """Patches sys.modules to simulate google.auth.aio existence."""
    mock_creds_module = unittest.mock.MagicMock()
    # We must set the base class to object so our wrapper can inherit safely in tests
    mock_creds_module.Credentials = object

    modules = {
        "google.auth.aio": unittest.mock.MagicMock(),
        "google.auth.aio.credentials": mock_creds_module,
    }

    with unittest.mock.patch.dict(sys.modules, modules):
        # We also need to manually flip the flag in the module to True for the test context
        # because the module was likely already imported with the flag set to False/True
        # depending on the real environment.
        with unittest.mock.patch.object(async_creds, "_AIO_AVAILABLE", True):
            # We also need to ensure BaseCredentials in the module points to our mock
            # if we want strictly correct inheritance, though duck typing usually suffices.
            with unittest.mock.patch.object(async_creds, "BaseCredentials", object):
                yield


@pytest.fixture
def mock_sync_creds():
    """Creates a mock of the synchronous Google Credentials object."""
    creds = unittest.mock.create_autospec(google_creds.Credentials, instance=True)
    type(creds).valid = unittest.mock.PropertyMock(return_value=True)
    return creds


@pytest.fixture
def async_wrapper(mock_aio_modules, mock_sync_creds):
    """Instantiates the wrapper with the mock credentials."""
    # This instantiation would raise ImportError if mock_aio_modules didn't set _AIO_AVAILABLE=True
    return async_creds.AsyncCredsWrapper(mock_sync_creds)


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
        with unittest.mock.patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = unittest.mock.AsyncMock()
            mock_get_loop.return_value = mock_loop

            await async_wrapper.refresh(None)

            mock_loop.run_in_executor.assert_called_once()
            args, _ = mock_loop.run_in_executor.call_args
            assert args[1] == mock_sync_creds.refresh

    @pytest.mark.asyncio
    async def test_before_request_valid_creds(self, async_wrapper, mock_sync_creds):
        """Test before_request when credentials are ALREADY valid."""
        type(mock_sync_creds).valid = unittest.mock.PropertyMock(return_value=True)

        headers = {}
        await async_wrapper.before_request(None, "GET", "http://example.com", headers)

        mock_sync_creds.apply.assert_called_once_with(headers)
        mock_sync_creds.before_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_before_request_invalid_creds(self, async_wrapper, mock_sync_creds):
        """Test before_request when credentials are INVALID (refresh path)."""
        type(mock_sync_creds).valid = unittest.mock.PropertyMock(return_value=False)

        headers = {}
        method = "GET"
        url = "http://example.com"

        with unittest.mock.patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = unittest.mock.AsyncMock()
            mock_get_loop.return_value = mock_loop

            await async_wrapper.before_request(None, method, url, headers)

            mock_loop.run_in_executor.assert_called_once()
            args, _ = mock_loop.run_in_executor.call_args
            assert args[1] == mock_sync_creds.before_request

    def test_missing_aio_raises_error(self, mock_sync_creds):
        """Ensure ImportError is raised if _AIO_AVAILABLE is False."""
        # We manually simulate the environment where AIO is missing
        with unittest.mock.patch.object(async_creds, "_AIO_AVAILABLE", False):
            with pytest.raises(ImportError) as excinfo:
                async_creds.AsyncCredsWrapper(mock_sync_creds)

            assert "Failed to import 'google.auth.aio'" in str(excinfo.value)
