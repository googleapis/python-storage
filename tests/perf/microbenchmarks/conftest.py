# from tests.system.conftest import blobs_to_delete

# __all__ = [

# "blobs_to_delete",
# ]

import contextlib
from typing import Any
from tests.perf.microbenchmarks.resource_monitor import ResourceMonitor
import pytest
from tests.system._helpers import delete_blob

import asyncio
import multiprocessing
import os
import uuid
from google.cloud import storage
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient

_OBJECT_NAME_PREFIX = "micro-benchmark"


@pytest.fixture(scope="function")
def blobs_to_delete():
    blobs_to_delete = []

    yield blobs_to_delete

    for blob in blobs_to_delete:
        delete_blob(blob)


@pytest.fixture(scope="session")
def storage_client():
    from google.cloud.storage import Client

    client = Client()
    with contextlib.closing(client):
        yield client

@pytest.fixture
def monitor():
    """
    Provides the ResourceMonitor class.
    Usage: with monitor() as m: ...
    """
    return ResourceMonitor

def publish_resource_metrics(benchmark: Any, monitor: ResourceMonitor) -> None:
    """
    Helper function to publish resource monitor results to the extra_info property.
    """
    benchmark.extra_info.update(
        {
            "cpu_max_global": f"{monitor.max_cpu:.2f}",
            "mem_max": f"{monitor.max_mem:.2f}",
            "net_throughput_mb_s": f"{monitor.throughput_mb_s:.2f}",
            "vcpus": monitor.vcpus,
        }
    )


async def upload_appendable_object(bucket_name, object_name, object_size, chunk_size):
    writer = AsyncAppendableObjectWriter(
        AsyncGrpcClient().grpc_client, bucket_name, object_name
    )
    await writer.open()
    uploaded_bytes = 0
    while uploaded_bytes < object_size:
        bytes_to_upload = min(chunk_size, object_size - uploaded_bytes)
        await writer.append(os.urandom(bytes_to_upload))
        uploaded_bytes += bytes_to_upload
    object_metdata = await writer.close(finalize_on_close=True)
    assert object_metdata.size == uploaded_bytes
    return uploaded_bytes


def _upload_worker(args):
    bucket_name, object_name, object_size, chunk_size = args
    uploaded_bytes = asyncio.run(
        upload_appendable_object(bucket_name, object_name, object_size, chunk_size)
    )
    return object_name, uploaded_bytes


def _create_files(num_files, bucket_name, object_size, chunk_size=128 * 1024 * 1024):
    """
    1. using upload_appendable_object implement this and return a list of file names.
    """
    object_names = [
        f"{_OBJECT_NAME_PREFIX}-{uuid.uuid4().hex[:5]}" for _ in range(num_files)
    ]

    args_list = [
        (bucket_name, object_names[i], object_size, chunk_size)
        for i in range(num_files)
    ]

    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool() as pool:
        results = pool.map(_upload_worker, args_list)

    total_uploaded_bytes = sum(r[1] for r in results)
    assert total_uploaded_bytes == object_size * num_files

    return [r[0] for r in results]


@pytest.fixture
def workload_params(request):
    params = request.param
    files_names = _create_files(
        params.num_files,
        params.bucket_name,
        params.file_size_bytes,
    )
    return params, files_names
