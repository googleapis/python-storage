"""
Docstring for tests.perf.microbenchmarks.test_writes

File for benchmarking zonal writes (i.e. uploads)
"""

import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import logging

import pytest
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import AsyncAppendableObjectWriter

from tests.perf.microbenchmarks._utils import publish_benchmark_extra_info, RandomBytesIO
from tests.perf.microbenchmarks.conftest import publish_resource_metrics
import tests.perf.microbenchmarks.config as config

# Get write parameters
all_params = config.get_write_params()

async def create_client():
    """Initializes async client and gets the current event loop."""
    return AsyncGrpcClient().grpc_client

async def upload_chunks_using_grpc_async(client, filename, other_params):
    start_time = time.monotonic_ns()

    writer = AsyncAppendableObjectWriter(
        client=client, bucket_name=other_params.bucket_name, object_name=filename
    )
    await writer.open()

    uploaded_bytes = 0
    upload_size = other_params.file_size_bytes
    chunk_size = other_params.chunk_size_bytes

    while uploaded_bytes < upload_size:
        bytes_to_upload = min(chunk_size, upload_size - uploaded_bytes)
        data = os.urandom(bytes_to_upload)
        await writer.append(data)
        uploaded_bytes += bytes_to_upload
    await writer.close()

    assert uploaded_bytes == upload_size
    
    end_time = time.monotonic_ns()
    elapsed_time = end_time - start_time
    return elapsed_time / 1_000_000_000

def upload_chunks_using_grpc(loop, client, filename, other_params):
    return loop.run_until_complete(
        upload_chunks_using_grpc_async(client, filename, other_params)
    )

def upload_using_json(_, json_client, filename, other_params):
    start_time = time.monotonic_ns()

    bucket = json_client.bucket(other_params.bucket_name)
    blob = bucket.blob(filename)
    upload_size = other_params.file_size_bytes
    # Don't use BytesIO because it'll report high memory usage for large files.
    # `RandomBytesIO` generates random bytes on the fly.
    in_mem_file = RandomBytesIO(upload_size)
    # data = os.urandom(upload_size)
    blob.upload_from_file(in_mem_file)

    end_time = time.monotonic_ns()
    elapsed_time = end_time - start_time
    return elapsed_time / 1_000_000_000

@pytest.mark.parametrize(
    "workload_params",
    all_params["write_seq"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_uploads_single_proc_single_coro(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    params, files_names = workload_params

    if params.bucket_type == "zonal":
        logging.info("bucket type zonal")
        target_func = upload_chunks_using_grpc
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = loop.run_until_complete(create_client())
    else:
        logging.info("bucket type regional")
        target_func = upload_using_json
        loop = None
        client = storage_client

    output_times = []

    def target_wrapper(*args, **kwargs):
        result = target_func(*args, **kwargs)
        output_times.append(result)
        return output_times

    try:
        with monitor() as m:
            output_times = benchmark.pedantic(
                target=target_wrapper,
                iterations=1,
                rounds=params.rounds,
                args=(
                    loop,
                    client,
                    files_names[0],
                    params,
                ),
            )
    finally:
        if loop is not None:
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()
    publish_benchmark_extra_info(benchmark, params, benchmark_group="write", true_times=output_times)
    publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )

def upload_files_using_grpc_multi_coro(loop, client, files, other_params):
    async def main():
        tasks = []
        for f in files:
            tasks.append(
                upload_chunks_using_grpc_async(client, f, other_params)
            )
        return await asyncio.gather(*tasks)

    results = loop.run_until_complete(main())
    return max(results)

def upload_files_using_json_multi_threaded(_, json_client, files, other_params):
    results = []
    with ThreadPoolExecutor(max_workers=other_params.num_coros) as executor:
        futures = []
        for f in files:
            future = executor.submit(
                upload_using_json, None, json_client, f, other_params
            )
            futures.append(future)

        for future in futures:
            results.append(future.result())

    return max(results)

@pytest.mark.parametrize(
    "workload_params",
    all_params["write_seq_multi_coros"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_uploads_single_proc_multi_coro(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    params, files_names = workload_params

    if params.bucket_type == "zonal":
        logging.info("bucket type zonal")
        target_func = upload_files_using_grpc_multi_coro
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = loop.run_until_complete(create_client())
    else:
        logging.info("bucket type regional")
        target_func = upload_files_using_json_multi_threaded
        loop = None
        client = storage_client

    output_times = []

    def target_wrapper(*args, **kwargs):
        result = target_func(*args, **kwargs)
        output_times.append(result)
        return output_times

    try:
        with monitor() as m:
            output_times = benchmark.pedantic(
                target=target_wrapper,
                iterations=1,
                rounds=params.rounds,
                args=(
                    loop,
                    client,
                    files_names,
                    params,
                ),
            )
    finally:
        if loop is not None:
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()
    publish_benchmark_extra_info(benchmark, params, benchmark_group="write", true_times=output_times)
    publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )

def _upload_files_worker(files_to_upload, other_params, bucket_type):
    if bucket_type == "zonal":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = loop.run_until_complete(create_client())
        try:
            result = upload_files_using_grpc_multi_coro(
                loop, client, files_to_upload, other_params
            )
        finally:
            # cleanup loop
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()
        return result
    else:  # regional
        from google.cloud import storage
        json_client = storage.Client()
        return upload_files_using_json_multi_threaded(
            None, json_client, files_to_upload, other_params
        )

def upload_files_mp_mc_wrapper(files_names, params):
    num_processes = params.num_processes
    num_coros = params.num_coros

    filenames_per_process = [
        files_names[i : i + num_coros] for i in range(0, len(files_names), num_coros)
    ]

    args = [
        (
            filenames,
            params,
            params.bucket_type,
        )
        for filenames in filenames_per_process
    ]

    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=num_processes) as pool:
        results = pool.starmap(_upload_files_worker, args)

    return max(results)

@pytest.mark.parametrize(
    "workload_params",
    all_params["write_seq_multi_process"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_uploads_multi_proc_multi_coro(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    params, files_names = workload_params

    output_times = []

    def target_wrapper(*args, **kwargs):
        result = upload_files_mp_mc_wrapper(*args, **kwargs)
        output_times.append(result)
        return output_times

    try:
        with monitor() as m:
            output_times = benchmark.pedantic(
                target=target_wrapper,
                iterations=1,
                rounds=params.rounds,
                args=(
                    files_names,
                    params,
                ),
            )
    finally:
        publish_benchmark_extra_info(benchmark, params, benchmark_group="write", true_times=output_times)
        publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )
