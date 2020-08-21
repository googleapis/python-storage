Metrics with OpenTelemetry
==================================
This library uses `OpenTelemetry <https://opentelemetry.io/>`_ to record metric information on API requests.
For more information on installing Cloud Monitoring, see the `Cloud Monitoring docs <https://google-cloud-opentelemetry.readthedocs.io/en/latest/examples/cloud_monitoring/README.html>`_.

We first need to install opentelemetry:

.. code-block:: sh

    pip install opentelemetry-api
    pip install opentelemetry-sdk
    pip install opentelemetry-exporter-google-cloud

(Optionally) You can install this package to augment your metrics with resource info.

.. code-block:: sh

    pip install opentelemetry-tools-google-cloud

Then, at the beginning of your application create a MeterProvider. Example:

.. code:: python

    # "opt-in" for opentelemtry metrics capturing.
    # Requires you to have installed opentelemetry packages and called set_meter_provider.
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider

    #==============================================================================
    # OPTIONAL: These lines of code will scrape resource info from the env/metadata.
    # This info will then be passed down the line and added to metric info.
    from opentelemetry.tools.resource_detector import GoogleCloudResourceDetector
    resources = GoogleCloudResourceDetector().detect()

    # Note that this will NOT work if you are on a cloudtop, as you are on a
    # VM instance that belongs to the project "cloudtop:prod" which you likely
    # don't have Cloud Monitoring write access to.
    #==============================================================================

    # If you don't want to capture resources, remove 'resource=resources'.
    metrics.set_meter_provider(MeterProvider(stateful=False, resource=resources))

    # Normal code below. This is your application / script.

Check out captured metrics at `Cloud Monitoring <https://console.cloud.google.com/monitoring/metrics-explorer>`_.
