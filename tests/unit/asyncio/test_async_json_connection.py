import sys
import pytest
import json
from unittest import mock
from google.cloud.storage import _http as storage_http
from google.api_core import exceptions
from google.auth.credentials import Credentials
from google.api_core.client_info import ClientInfo
from google.cloud.storage._experimental.asyncio.utility.async_json_connection import (
    AsyncJSONConnection,
)

pytestmark = pytest.mark.skipif(
    sys.version_info[:2] == (3, 9), reason="Not supported on 3.9"
)


class MockAuthResponse:
    """Simulates google.auth.aio.transport.aiohttp.Response."""

    def __init__(self, status_code=200, data=b"{}", headers=None):
        self.status_code = status_code
        self._data = data
        self._headers = headers or {}

    @property
    def headers(self):
        return self._headers

    async def read(self):
        return self._data


def _make_credentials():
    creds = mock.Mock(spec=Credentials)
    creds.universe_domain = "googleapis.com"
    return creds


@pytest.fixture
def async_connection():
    """Creates an instance of AsyncJSONConnection with a mocked client."""
    return AsyncJSONConnection(mock.Mock(), _async_http=mock.AsyncMock())


@pytest.fixture
def mock_trace_span():
    """Mocks the OpenTelemetry trace span context manager."""
    target = "google.cloud.storage._experimental.asyncio.utility.async_json_connection.create_trace_span"
    with mock.patch(target) as mock_span:
        mock_span.return_value.__enter__.return_value = None
        yield mock_span


def test_init_defaults(async_connection):
    """Test initialization with default values."""
    assert isinstance(async_connection._client_info, ClientInfo)
    assert async_connection.API_BASE_URL == storage_http.Connection.DEFAULT_API_ENDPOINT
    assert async_connection.API_VERSION == storage_http.Connection.API_VERSION
    assert async_connection.API_URL_TEMPLATE == storage_http.Connection.API_URL_TEMPLATE
    assert "gcloud-python" in async_connection.user_agent


def test_init_custom_endpoint():
    """Test initialization with a custom API endpoint."""
    custom_endpoint = "https://custom.storage.googleapis.com"
    conn = AsyncJSONConnection(mock.Mock(), api_endpoint=custom_endpoint)
    assert conn.API_BASE_URL == custom_endpoint


def test_passing_async_http_uses_the_same_async_http():
    async_http = mock.Mock()
    conn = AsyncJSONConnection(mock.Mock(), _async_http=async_http)
    assert conn.async_http == async_http


@pytest.mark.asyncio
async def test_not_passing_async_http_creates_new():
    with mock.patch(
        "google.cloud.storage._experimental.asyncio.utility.async_json_connection.AsyncSession"
    ) as MockSession:
        conn = AsyncJSONConnection(
            mock.Mock(), _async_http=None, credentials=_make_credentials()
        )
        assert conn.async_http is MockSession.return_value


@pytest.mark.asyncio
async def test_close_async_json_connection():
    with mock.patch(
        "google.cloud.storage._experimental.asyncio.utility.async_json_connection.AsyncSession"
    ):
        conn = AsyncJSONConnection(
            mock.Mock(), _async_http=None, credentials=_make_credentials()
        )

        internal_mock = mock.AsyncMock()
        conn._async_http_internal = internal_mock
        await conn.close()
        internal_mock.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_manages_internal_session():
    """Tests that close() is called on an internally created session."""
    with mock.patch(
        "google.cloud.storage._experimental.asyncio.utility.async_json_connection.AsyncSession"
    ):
        conn = AsyncJSONConnection(
            mock.Mock(), _async_http=None, credentials=_make_credentials()
        )

        # Force session creation
        session = conn.async_http
        session.close = mock.AsyncMock()  # Make it an async mock

        await conn.close()
        session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_ignores_user_session():
    """Tests that close() is NOT called on a user-provided session."""
    user_session = mock.AsyncMock()
    conn = AsyncJSONConnection(
        mock.Mock(), _async_http=user_session, credentials=_make_credentials()
    )

    await conn.close()
    user_session.close.assert_not_awaited()


def test_extra_headers_property(async_connection):
    """Test getter and setter for extra_headers."""
    headers = {"X-Custom-Header": "value"}
    async_connection.extra_headers = headers
    assert async_connection.extra_headers == headers


def test_build_api_url_simple(async_connection):
    """Test building a simple API URL."""
    url = async_connection.build_api_url(path="/b/bucket-name")
    expected = (
        f"{async_connection.API_BASE_URL}/storage/v1/b/bucket-name?prettyPrint=false"
    )
    assert url == expected


def test_build_api_url_with_params(async_connection):
    """Test building an API URL with query parameters."""
    params = {"projection": "full", "versions": True}
    url = async_connection.build_api_url(path="/b/bucket", query_params=params)

    assert "projection=full" in url
    assert "versions=True" in url
    assert "prettyPrint=false" in url


@pytest.mark.asyncio
async def test_make_request_headers(async_connection):
    """Test that _make_request adds the correct headers."""
    mock_response = MockAuthResponse(status_code=200)
    async_connection.async_http.request.return_value = mock_response

    async_connection.user_agent = "test-agent/1.0"
    async_connection.extra_headers = {"X-Test": "True"}

    await async_connection._make_request(
        method="GET", url="http://example.com", content_type="application/json"
    )

    call_args = async_connection.async_http.request.call_args
    _, kwargs = call_args
    headers = kwargs["headers"]

    assert headers["Content-Type"] == "application/json"
    assert headers["Accept-Encoding"] == "gzip"

    assert "test-agent/1.0" in headers["User-Agent"]

    assert headers["X-Test"] == "True"


@pytest.mark.asyncio
async def test_api_request_success(async_connection, mock_trace_span):
    """Test the high-level api_request method wraps the call correctly."""
    expected_data = {"items": []}
    mock_response = MockAuthResponse(
        status_code=200, data=json.dumps(expected_data).encode("utf-8")
    )
    async_connection.async_http.request.return_value = mock_response

    response = await async_connection.api_request(method="GET", path="/b/bucket")

    assert response == expected_data
    mock_trace_span.assert_called_once()


@pytest.mark.asyncio
async def test_perform_api_request_json_serialization(async_connection):
    """Test that dictionary data is serialized to JSON."""
    mock_response = MockAuthResponse(status_code=200)
    async_connection.async_http.request.return_value = mock_response

    data = {"key": "value"}
    await async_connection.api_request(method="POST", path="/b", data=data)

    call_args = async_connection.async_http.request.call_args
    _, kwargs = call_args

    assert kwargs["data"] == json.dumps(data)
    assert kwargs["headers"]["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_perform_api_request_error_handling(async_connection):
    """Test that non-2xx responses raise GoogleAPICallError."""
    error_json = {"error": {"message": "Not Found"}}
    mock_response = MockAuthResponse(
        status_code=404, data=json.dumps(error_json).encode("utf-8")
    )
    async_connection.async_http.request.return_value = mock_response

    with pytest.raises(exceptions.GoogleAPICallError) as excinfo:
        await async_connection.api_request(method="GET", path="/b/nonexistent")

    assert "Not Found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_perform_api_request_no_json_response(async_connection):
    """Test response handling when expect_json is False."""
    raw_bytes = b"binary_data"
    mock_response = MockAuthResponse(status_code=200, data=raw_bytes)
    async_connection.async_http.request.return_value = mock_response

    response = await async_connection.api_request(
        method="GET", path="/b/obj", expect_json=False
    )

    assert response == raw_bytes


@pytest.mark.asyncio
async def test_api_request_with_retry(async_connection):
    """Test that the retry policy is applied if conditions are met."""
    mock_response = MockAuthResponse(status_code=200, data=b"{}")
    async_connection.async_http.request.return_value = mock_response

    mock_retry = mock.Mock()
    mock_policy = mock.Mock(side_effect=lambda call: call)
    mock_retry.get_retry_policy_if_conditions_met.return_value = mock_policy

    await async_connection.api_request(method="GET", path="/b/bucket", retry=mock_retry)

    mock_retry.get_retry_policy_if_conditions_met.assert_called_once()
    mock_policy.assert_called_once()


def test_build_api_url_repeated_params(async_connection):
    """Test building URL with a list of tuples (repeated keys)."""
    params = [("field", "name"), ("field", "size")]
    url = async_connection.build_api_url(path="/b/bucket", query_params=params)

    assert "field=name" in url
    assert "field=size" in url
    assert url.count("field=") == 2


def test_build_api_url_overrides(async_connection):
    """Test building URL with explicit base URL and version overrides."""
    url = async_connection.build_api_url(
        path="/b/bucket", api_base_url="https://example.com", api_version="v2"
    )
    assert "https://example.com/storage/v2/b/bucket" in url


@pytest.mark.asyncio
async def test_perform_api_request_empty_response(async_connection):
    """Test handling of empty 2xx response when expecting JSON."""
    mock_response = MockAuthResponse(status_code=204, data=b"")
    async_connection.async_http.request.return_value = mock_response

    response = await async_connection.api_request(
        method="DELETE", path="/b/bucket/o/object"
    )

    assert response == {}


@pytest.mark.asyncio
async def test_perform_api_request_non_json_error(async_connection):
    """Test error handling when the error response is plain text (not JSON)."""
    error_text = "Bad Gateway"
    mock_response = MockAuthResponse(status_code=502, data=error_text.encode("utf-8"))
    async_connection.async_http.request.return_value = mock_response

    with pytest.raises(exceptions.GoogleAPICallError) as excinfo:
        await async_connection.api_request(method="GET", path="/b/bucket")

    assert error_text in str(excinfo.value)
    assert excinfo.value.code == 502


@pytest.mark.asyncio
async def test_make_request_extra_api_info(async_connection):
    """Test logic for constructing x-goog-api-client header with extra info."""
    mock_response = MockAuthResponse(status_code=200)
    async_connection.async_http.request.return_value = mock_response

    invocation_id = "test-id-123"

    await async_connection._make_request(
        method="GET", url="http://example.com", extra_api_info=invocation_id
    )

    call_args = async_connection.async_http.request.call_args
    _, kwargs = call_args
    headers = kwargs["headers"]

    client_header = headers.get("X-Goog-API-Client")
    assert async_connection.user_agent in client_header
    assert invocation_id in client_header


def test_user_agent_setter(async_connection):
    """Test explicit setter for user_agent."""
    new_ua = "my-custom-app/1.0"
    async_connection.user_agent = new_ua
    assert new_ua in async_connection.user_agent
    assert async_connection._client_info.user_agent == new_ua
