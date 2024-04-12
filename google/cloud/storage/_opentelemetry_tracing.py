"""Manages OpenTelemetry tracing span creation and handling."""

import logging
import os

from contextlib import contextmanager

from google.api_core import exceptions as api_exceptions
from google.api_core import retry as api_retry
from google.cloud.storage import __version__


ENABLE_OTEL_TRACES_ENV_VAR = "ENABLE_GCS_PYTHON_CLIENT_OTEL_TRACES"
_DEFAULT_ENABLE_OTEL_TRACES_VALUE = False

enable_otel_traces = os.environ.get(
    ENABLE_OTEL_TRACES_ENV_VAR, _DEFAULT_ENABLE_OTEL_TRACES_VALUE
)
logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace

    HAS_OPENTELEMETRY = True

    logger.info(f"HAS_OPENTELEMETRY is {HAS_OPENTELEMETRY}")
except ImportError:
    logger.debug(
        "This service is instrumented using OpenTelemetry. "
        "OpenTelemetry or one of its components could not be imported; "
        "please add compatible versions of opentelemetry-api and "
        "opentelemetry-instrumentation packages in order to get Storage "
        "Tracing data."
    )
    HAS_OPENTELEMETRY = False

_default_attributes = {
    "rpc.service": "CloudStorage",
    "rpc.system": "http",
    "user_agent.original": f"gcloud-python/{__version__}",
}


@contextmanager
def create_span(
    name, attributes=None, client=None, api_request=None, retry=None, **kwargs
):
    """Creates a context manager for a new span and set it as the current span
    in the configured tracer. If no configuration exists yields None."""
    if not HAS_OPENTELEMETRY or not enable_otel_traces:
        print(f"HAS_OPENTELEMETRY is {HAS_OPENTELEMETRY}")
        print(f"enable_otel_traces is {enable_otel_traces}")
        yield None
        return

    tracer = trace.get_tracer(__name__)
    final_attributes = _get_final_attributes(attributes, client, api_request, retry)
    # Yield new span.
    with tracer.start_as_current_span(
        name=name, kind=trace.SpanKind.CLIENT, attributes=final_attributes
    ) as span:
        try:
            yield span
        except api_exceptions.GoogleAPICallError as error:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.record_exception(error)
            raise error


def _get_final_attributes(attributes=None, client=None, api_request=None, retry=None):
    collected_attr = _default_attributes.copy()
    if api_request:
        collected_attr.update(_set_api_request_attr(api_request, client))
    if isinstance(retry, api_retry.Retry):
        collected_attr.update(_set_retry_attr(retry))
    if attributes:
        collected_attr.update(attributes)
    final_attributes = {k: v for k, v in collected_attr.items() if v is not None}
    return final_attributes


def _set_api_request_attr(request, client):
    attr = {}
    if request.get("method"):
        attr["http.request.method"] = request.get("method")
    if request.get("path"):
        path = request.get("path")
        full_path = f"{client._connection.API_BASE_URL}{path}"
        attr["url.full"] = full_path
    if request.get("query_params"):
        attr["http.request.query_params"] = request.get("query_params")
    if request.get("headers"):
        attr["http.request.headers"] = request.get("headers")
    if request.get("timeout"):
        attr["connect_timeout,read_timeout"] = request.get("timeout")
    return attr


def _set_retry_attr(retry):
    retry_info = f"multiplier{retry._multiplier}/deadline{retry._deadline}/max{retry._maximum}/initial{retry._initial}/predicate{retry._predicate}"
    return {"retry": retry_info}
