Metrics with OpenTelemetry
==================================
This library uses `OpenTelemetry <https://opentelemetry.io/>`_ to record metric information on API requests.
For information on the benefits and utility of tracing, see the `Cloud Monitoring docs <https://cloud.google.com/monitoring/docs>`_.

We first need to install opentelemetry:

.. code-block:: sh

    pip install opentelemetry-api
    pip install opentelemetry-sdk
    pip install opentelemetry-exporter-google-cloud
    pip install opentelemetry-tools-google-cloud

Then, at the beginning of your application create a MeterProvider. Example:

.. code:: python

    # "opt-in" for opentelemtry metrics capturing.
    # Requires you to have installed opentelemetry packages and called set_meter_provider
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider

    #==============================================================================
    # OPTIONAL: These lines of code will detect + scrape resource info from the env/metadata.
    # This info will then be passed down the line and added to metric info
    from opentelemetry.tools.resource_detector import GoogleCloudResourceDetector
    resources = GoogleCloudResourceDetector().detect()

    # Note that this will NOT work if you are on a cloudtop, as you are on a
    # VM instacne that belongs to the project "cloudtop:prod" which you likely
    # don't have read access for
    #==============================================================================

    # If you don't use resources, remove resource=resources
    metrics.set_meter_provider(MeterProvider(stateful=False, resource=resources))

    # Normal code below. This is your application / script

Check out captured metrics at `Cloud Monitoring <https://pantheon.corp.google.com/monitoring/metrics-explorer>`_.