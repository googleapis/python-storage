# Copyright 2021 Google LLC
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


import uuid

from google.cloud import storage

import pytest

import storage_list_bucket_notifications
import storage_print_pubsub_bucket_notification

_topic_name = f"notification-{uuid.uuid4()}"


@pytest.fixture(scope="module")
def storage_client():
    return storage.Client()


@pytest.fixture(scope="module")
def publisher_client():
    try:
        from google.cloud.pubsub_v1 import PublisherClient
    except ImportError:
        pytest.skip("Cannot import pubsub")

    return PublisherClient()


@pytest.fixture(scope="module")
def notification_topic(storage_client, publisher_client):
    topic_path = publisher_client.topic_path(storage_client.project, _topic_name)
    publisher_client.create_topic(request={"name": topic_path})
    policy = publisher_client.get_iam_policy(request={"resource": topic_path})
    binding = policy.bindings.add()
    binding.role = "roles/pubsub.publisher"
    binding.members.append(
        "serviceAccount:{}".format(storage_client.get_service_account_email())
    )
    publisher_client.set_iam_policy(request={"resource": topic_path, "policy": policy})


@pytest.fixture(scope="module")
def bucket_w_notification(storage_client, notification_topic):
    """Yields a bucket with notification that is deleted after the tests complete."""
    bucket = None
    while bucket is None or bucket.exists():
        bucket_name = f"notification-test-{uuid.uuid4()}"
        bucket = storage_client.bucket(bucket_name)
    bucket.create()
    notification = bucket.notification(topic_name=_topic_name)
    notification.create()
    yield bucket
    bucket.delete(force=True)


def test_list_bucket_notifications(bucket_w_notification, capsys):
    storage_list_bucket_notifications.list_bucket_notifications(bucket_w_notification.name)
    out, _ = capsys.readouterr()
    assert "Notification ID" in out


def test_print_pubsub_bucket_notification(bucket_w_notification, capsys):
    notification_id = 1
    storage_print_pubsub_bucket_notification.print_pubsub_bucket_notification(bucket_w_notification.name, notification_id)
    out, _ = capsys.readouterr()
    assert "Notification ID: 1" in out
