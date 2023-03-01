Python Client for Google Cloud Storage
======================================

|stable| |pypi| |versions|

`Google Cloud Storage`_ is a managed service for storing unstructured data. Cloud Storage
allows world-wide storage and retrieval of any amount of data at any time. You can use
Cloud Storage for a range of scenarios including serving website content, storing data
for archival and disaster recovery, or distributing large data objects to users via direct download.

A comprehensive list of changes in each version may be found in the `CHANGELOG`_.

- `Product Documentation`_
- `Client Library Documentation`_
- `github.com/googleapis/python-storage`_

Read more about the client libraries for Cloud APIs, including the older
Google APIs Client Libraries, in `Client Libraries Explained`_.

.. |stable| image:: https://img.shields.io/badge/support-stable-gold.svg
   :target: https://github.com/googleapis/google-cloud-python/blob/main/README.rst#stability-levels
.. |pypi| image:: https://img.shields.io/pypi/v/google-cloud-storage.svg
   :target: https://pypi.org/project/google-cloud-storage/
.. |versions| image:: https://img.shields.io/pypi/pyversions/google-cloud-storage.svg
   :target: https://pypi.org/project/google-cloud-storage/
.. _Google Cloud Storage: https://cloud.google.com/storage
.. _Client Library Documentation: https://cloud.google.com/python/docs/reference/storage/latest
.. _Product Documentation:  https://cloud.google.com/storage
.. _CHANGELOG:  https://github.com/googleapis/python-storage/blob/main/CHANGELOG.md
.. _github.com/googleapis/python-storage: https://github.com/googleapis/python-storage
.. _Client Libraries Explained: https://cloud.google.com/apis/docs/client-libraries-explained

Quick Start
-----------

In order to use this library, you first need to go through the following steps.
A step-by-step guide may also be found in `Get Started with Client Libraries`_.

1. `Select or create a Cloud Platform project.`_
2. `Enable billing for your project.`_
3. `Enable the Google Cloud Storage API.`_
4. `Setup Authentication.`_

.. _Get Started with Client Libraries: https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python
.. _Select or create a Cloud Platform project.: https://console.cloud.google.com/project
.. _Enable billing for your project.: https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project
.. _Enable the Google Cloud Storage API.:  https://console.cloud.google.com/flows/enableapi?apiid=storage-api.googleapis.com
.. _Setup Authentication.: https://cloud.google.com/docs/authentication/client-libraries

Installation
~~~~~~~~~~~~

Install this library in a virtual environment using `venv`_. `venv`_ is a tool that
creates isolated Python environments. These isolated environments can have separate
versions of Python packages, which allows you to isolate one project's dependencies
from the dependencies of other projects.

With `venv`_, it's possible to install this library without needing system
install permissions, and without clashing with the installed system
dependencies.

.. _`venv`: https://docs.python.org/3/library/venv.html


Code samples and snippets
~~~~~~~~~~~~~~~~~~~~~~~~~

Code samples and snippets live in the `samples/`_ folder.

.. _`samples/`: https://github.com/googleapis/python-storage/tree/main/samples


Supported Python Versions
^^^^^^^^^^^^^^^^^^^^^^^^^
Our client libraries are compatible with all current `active`_ and `maintenance`_ versions of
Python.

Python >= 3.7

.. _active: https://devguide.python.org/devcycle/#in-development-main-branch
.. _maintenance: https://devguide.python.org/devcycle/#maintenance-branches

Unsupported Python Versions
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Python <= 3.6

If you are using an `end-of-life`_
version of Python, we recommend that you update as soon as possible to an actively supported version.

.. _end-of-life: https://devguide.python.org/devcycle/#end-of-life-branches

Mac/Linux
^^^^^^^^^

.. code-block:: console

    python3 -m venv <your-env>
    source <your-env>/bin/activate
    pip install google-cloud-storage


Windows
^^^^^^^

.. code-block:: console

    py -m venv <your-env>
    .\<your-env>\Scripts\activate
    pip install google-cloud-storage

Next Steps
~~~~~~~~~~

-  Read the `Google Cloud Storage Product documentation`_ to learn
   more about the product and see How-to Guides.
-  Read the `Client Library Documentation`_ for Google Cloud Storage API
   to see other available methods on the client.
-  View this `README`_ to see the full list of Cloud
   APIs that we cover.

.. _Google Cloud Storage Product documentation:  https://cloud.google.com/storage
.. _README: https://github.com/googleapis/google-cloud-python/blob/main/README.rst
