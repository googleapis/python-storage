# -*- coding: utf-8 -*-
#
# Copyright 2017 Google LLC
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

import importlib
import sys
import unittest

from mock import patch
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider, Counter

from google.cloud.storage import _opentelemetry_meter
from tests.unit.test_blob import Test_Blob


# Just to make things more succinct
def ot_wrapped(*args, **kwargs):
    return _opentelemetry_meter.telemetry_wrapped_api_request(*args, **kwargs)


def mock_api_request(*args, **kwargs):
    return args, kwargs


class TestNoOpentelemtryPackage(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # "uninstall" opentelemetry
        self._temp_opentelemetry = sys.modules["opentelemetry"]

        sys.modules["opentelemetry"] = None
        importlib.reload(_opentelemetry_meter)

    @classmethod
    def tearDownClass(self):
        sys.modules["opentelemetry"] = self._temp_opentelemetry
        importlib.reload(_opentelemetry_meter)

    def test_not_initialized(self):
        self.assertFalse(_opentelemetry_meter.OPENTELEMETRY_READY)
        # Opentelemetry objects shouldn't be initialized
        self.assertRaises(AttributeError, lambda: _opentelemetry_meter.meter)

    def test_wrapped_api_request(self):
        self.assertEqual(
            ot_wrapped(mock_api_request, "arg1", kwarg1="kwarg1"),
            (("arg1",), {"kwarg1": "kwarg1"}),
        )
        self.assertEqual(
            ot_wrapped(
                mock_api_request,
                "arg1",
                kwarg1="kwarg1",
                **{_opentelemetry_meter.FUNCTION_NAME_KEY: "hi"}
            ),
            (("arg1",), {"kwarg1": "kwarg1"}),
        )


class TestNoMeterProvider(unittest.TestCase):
    def test_not_initialized(self):
        self.assertFalse(_opentelemetry_meter.OPENTELEMETRY_READY)
        # Opentelemetry objects shouldn't be initialized without meter_provider
        self.assertRaises(AttributeError, lambda: _opentelemetry_meter.meter)

    def test_wrapped_api_request(self):
        self.assertEqual(
            ot_wrapped(mock_api_request, "arg1", kwarg1="kwarg1"),
            (("arg1",), {"kwarg1": "kwarg1"}),
        )
        self.assertEqual(
            ot_wrapped(
                mock_api_request,
                "arg1",
                kwarg1="kwarg1",
                **{_opentelemetry_meter.FUNCTION_NAME_KEY: "hi"}
            ),
            (("arg1",), {"kwarg1": "kwarg1"}),
        )


class TestOpenTelemetryBase(Test_Blob):
    @classmethod
    def setUpClass(self):
        meter_provider = MeterProvider(stateful=False)
        # Make starting the exporter thread a no-op
        meter_provider.start_pipeline = lambda *args, **kwargs: None
        metrics._METER_PROVIDER = meter_provider
        importlib.reload(_opentelemetry_meter)

    @classmethod
    def tearDownClass(self):
        metrics._METER_PROVIDER = metrics.DefaultMeterProvider()
        importlib.reload(_opentelemetry_meter)


class TestOpenTelemetryMetrics(TestOpenTelemetryBase):
    def test_initialized(self):
        self.assertTrue(_opentelemetry_meter.OPENTELEMETRY_READY)
        self.assertIsNotNone(_opentelemetry_meter.requests_counter)

    @patch.object(Counter, "add")
    def test_wrapped_api_request(self, request_counter):
        self.assertEqual(
            ot_wrapped(mock_api_request, "arg1", kwarg1="kwarg1"),
            (("arg1",), {"kwarg1": "kwarg1"}),
        )
        self.assertEqual(
            ot_wrapped(
                mock_api_request,
                "arg1",
                kwarg1="kwarg1",
                **{_opentelemetry_meter.FUNCTION_NAME_KEY: "hi"}
            ),
            (("arg1",), {"kwarg1": "kwarg1"}),
        )
        self.assertEqual(request_counter.call_count, 2)

    @patch.object(Counter, "add")
    def test_wrapped_api_request_with_function_name(self, request_counter):
        from google.cloud.storage._opentelemetry_meter import FUNCTION_NAME_KEY

        self.assertEqual(
            ot_wrapped(mock_api_request, "arg1", **{FUNCTION_NAME_KEY: "foo"}),
            (("arg1",), {}),
        )
        self.assertEqual(
            request_counter.call_args_list[0][0], (1, {"function_name": "foo"})
        )

    @patch.object(Counter, "add")
    def test_wrapped_api_request_with_path(self, request_counter):
        self.assertEqual(
            ot_wrapped(mock_api_request, "arg1", path="foo", method="GET"),
            (("arg1",), {"path": "foo", "method": "GET"}),
        )
        self.assertEqual(
            request_counter.call_args_list[0][0], (1, {"function_name": "GET foo"})
        )

    @patch.object(Counter, "add")
    def test_download_with_chunks(self, request_counter):
        self._do_download_helper_w_chunks(False, False)
        self.assertEqual(
            request_counter.call_args_list[0][0], (1, {"function_name": "GET foo"})
        )
