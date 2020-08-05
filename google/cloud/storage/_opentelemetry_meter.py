# Copyright 2014 Google LLC
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

"""Manages OpenTelemetry trace creation and handling"""

try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import Counter, MeterProvider
    from opentelemetry.exporter.cloud_monitoring import (
        CloudMonitoringMetricsExporter,
    )

    HAS_OPENTELEMETRY_INSTALLED = True
except ImportError:
    HAS_OPENTELEMETRY_INSTALLED = False

instruments_setup = False
requests_counter = None

def setup_instruments():
    global requests_counter, instruments_setup
    meter = metrics.get_meter(__name__)
    metrics.get_meter_provider().start_pipeline(
        meter, CloudMonitoringMetricsExporter(), 10
    )
    requests_counter = meter.create_metric(
        name="GCS_request_counter",
        description="number of requests",
        unit="1",
        value_type=int,
        metric_type=Counter,
        label_keys=("path"),
    )
    instruments_setup = True


def telemetry_wrapped_api_request(api_request, **kwargs):
    if HAS_OPENTELEMETRY_INSTALLED:
        if not instruments_setup:
            setup_instruments()
        requests_counter.add(1, {'path': kwargs['path']})
    return api_request(**kwargs)
