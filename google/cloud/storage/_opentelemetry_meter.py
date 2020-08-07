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

"""Manages OpenTelemetry metrics creation and handling"""

try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import Counter, MeterProvider
    from opentelemetry.exporter.cloud_monitoring import (
        CloudMonitoringMetricsExporter,
    )

    HAS_OPENTELEMETRY_INSTALLED = True
except ImportError:
    HAS_OPENTELEMETRY_INSTALLED = False


if HAS_OPENTELEMETRY_INSTALLED:
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
    )

    def telemetry_wrapped_api_request(api_request, *args, **kwargs):
        print(api_request)
        requests_counter.add(1, {})
        return api_request(*args, **kwargs)
else:
    def telemetry_wrapped_api_request(api_request, *args, **kwargs):
        return api_request(*args, **kwargs)
