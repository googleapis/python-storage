"""
Docstring for tests.perf.microbenchmarks.test_reads

File for benchmarking zonal reads (i.e. downloads)

1. 1 object 1 coro with variable chunk_size

calculate latency, throughput, etc for downloads.


"""

import os
import time
import asyncio
import math
import random
from io import BytesIO
import logging

import pytest
from google.api_core import exceptions
from google.cloud.storage.blob import Blob

from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
from tests.perf.microbenchmarks._utils import publish_benchmark_extra_info
from tests.perf.microbenchmarks.conftest import (
    publish_resource_metrics,
)
import tests.perf.microbenchmarks.config as config

all_zonal_params = config._get_params()
print(all_zonal_params["read_rand"])
all_regional_params = config._get_params(bucket_type_filter="regional")


async def create_client():
    """Initializes async client and gets the current event loop."""
    return AsyncGrpcClient().grpc_client


async def _download_range_async(
    client, bucket_name, object_name, offset, size, chunk_size
):
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()
    output_buffer = BytesIO()

    remaining_size = size
    current_offset = offset

    while remaining_size > 0:
        bytes_to_download = min(chunk_size, remaining_size)
        await mrd.download_ranges([(current_offset, bytes_to_download, output_buffer)])
        remaining_size -= bytes_to_download
        current_offset += bytes_to_download

    await mrd.close()
    return output_buffer.getbuffer().nbytes


def download_one_object_in_parts(loop, client, filename, other_params):
    """
    1. each object will be divide equally (almost to adjust remainder) among coroutinges = `other_params.num_coros` and
    send to each coroutine.
    2. each coroutine downloads that range of the object,
    3. each coroutine returns bytes downloaded.
    4. sum of all bytes == object size

    """
    object_size = other_params.file_size_bytes
    num_coros = other_params.num_coros
    bucket_name = other_params.bucket_name
    chunk_size = other_params.chunk_size_bytes

    # Calculate ranges
    range_size = (object_size + num_coros - 1) // num_coros
    ranges = []
    for i in range(num_coros):
        offset = i * range_size
        size = min(range_size, object_size - offset)
        if size <= 0:
            break
        ranges.append((offset, size))

    async def main():
        tasks = []
        for offset, size in ranges:
            tasks.append(
                _download_range_async(
                    client, bucket_name, filename, offset, size, chunk_size
                )
            )

        results = await asyncio.gather(*tasks)
        total_downloaded = sum(results)
        assert total_downloaded == object_size

    loop.run_until_complete(main())


import multiprocessing


def _download_in_parts_worker(bucket_name, object_name, ranges, chunk_size):

    async def main():
        client = await create_client()
        tasks = []
        for offset, size in ranges:
            tasks.append(
                _download_range_async(
                    client, bucket_name, object_name, offset, size, chunk_size
                )
            )

        results = await asyncio.gather(*tasks)
        return sum(results)

    return asyncio.run(main())


def download_one_object_in_mn_parts(filename, other_params):
    """
    this method downloads one object in m*n parts where
    m = num_processes
    n = num_coros
    """
    object_size = other_params.file_size_bytes
    num_processes = other_params.num_processes
    num_coros = other_params.num_coros
    bucket_name = other_params.bucket_name
    chunk_size = other_params.chunk_size_bytes

    total_parts = num_processes * num_coros
    part_size = (object_size + total_parts - 1) // total_parts

    all_ranges = []
    for i in range(total_parts):
        offset = i * part_size
        size = min(part_size, object_size - offset)
        if size <= 0:
            break
        all_ranges.append((offset, size))

    # Distribute ranges to processes
    ranges_per_process = [
        all_ranges[i : i + num_coros] for i in range(0, len(all_ranges), num_coros)
    ]

    args = [
        (bucket_name, filename, ranges, chunk_size) for ranges in ranges_per_process
    ]
    multiprocessing.set_start_method("spawn", force=True)
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(_download_in_parts_worker, args)

    total_downloaded = sum(results)
    assert total_downloaded == object_size


async def _download_object_async(
    client, bucket_name, object_name, object_size, chunk_size
):
    return await _download_range_async(
        client, bucket_name, object_name, 0, object_size, chunk_size
    )


def _download_objects_worker(bucket_name, object_names, object_size, chunk_size):
    async def main():
        client = await create_client()
        tasks = []
        for object_name in object_names:
            tasks.append(
                _download_object_async(
                    client, bucket_name, object_name, object_size, chunk_size
                )
            )
        results = await asyncio.gather(*tasks)
        return sum(results)

    return asyncio.run(main())


async def _download_object_async_random(
    client, bucket_name, object_name, object_size, chunk_size
):
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()

    # 1. Generate chunks
    num_chunks = math.ceil(object_size / chunk_size)
    chunks_to_download = []
    for i in range(num_chunks):
        offset = i * chunk_size
        size = min(chunk_size, object_size - offset)
        chunks_to_download.append((offset, size))

    # 2. Shuffle chunks
    random.shuffle(chunks_to_download)

    downloaded_chunks = {}
    total_downloaded = 0

    for offset, size in chunks_to_download:
        chunk_buffer = BytesIO()
        await mrd.download_ranges([(offset, size, chunk_buffer)])
        downloaded_chunks[offset] = chunk_buffer.getvalue()
        total_downloaded += len(downloaded_chunks[offset])

    await mrd.close()
    assert total_downloaded == object_size
    return total_downloaded


def _download_objects_worker_random(bucket_name, object_names, object_size, chunk_size):
    async def main():
        client = await create_client()
        tasks = []
        for object_name in object_names:
            tasks.append(
                _download_object_async_random(
                    client, bucket_name, object_name, object_size, chunk_size
                )
            )
        results = await asyncio.gather(*tasks)
        return sum(results)

    return asyncio.run(main())


def download_mn_objects_using_m_process_n_coros_random(filenames, other_params):
    """

    there are m*n objects , distribute them among m process and n coroutine.
    Each processs should run `n` coro simultaneously and download one entire object.


    However, `download_mn_objects_using_m_process_n_coros` unlike each coroutine
    should divide the entire object size into chunks of `other_params.chunk_size_bytes` and randomly issues
    calls to `mrd.download_ranges` for all chunks.

    essentially get all chunks, shuffle chunks and call download_ranges.

    all object sizes are same.
    """
    num_processes = other_params.num_processes  # m
    num_coros = other_params.num_coros  # n
    bucket_name = other_params.bucket_name
    object_size = other_params.file_size_bytes
    chunk_size = other_params.chunk_size_bytes

    # Distribute filenames to processes
    filenames_per_process = [
        filenames[i : i + num_coros] for i in range(0, len(filenames), num_coros)
    ]

    args = [
        (bucket_name, names, object_size, chunk_size) for names in filenames_per_process
    ]

    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=num_processes) as pool:
        results = pool.starmap(_download_objects_worker_random, args)

    total_downloaded = sum(results)
    expected_download = len(filenames) * object_size
    assert total_downloaded == expected_download


def download_mn_objects_using_m_process_n_coros(filenames, other_params):
    """
    Docstring for download_mn_objects_using_m_process_n_coros

    there are m*n objects , distribute them among m process and n coroutine.
    Each processs should run `n` coro simultaneously and download one entire object.

    all object sizes are same.
    """
    num_processes = other_params.num_processes  # m
    num_coros = other_params.num_coros  # n
    bucket_name = other_params.bucket_name
    object_size = other_params.file_size_bytes
    chunk_size = other_params.chunk_size_bytes

    # Distribute filenames to processes
    filenames_per_process = [
        filenames[i : i + num_coros] for i in range(0, len(filenames), num_coros)
    ]

    args = [
        (bucket_name, names, object_size, chunk_size) for names in filenames_per_process
    ]

    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=num_processes) as pool:
        results = pool.starmap(_download_objects_worker, args)

    total_downloaded = sum(results)
    expected_download = len(filenames) * object_size
    assert total_downloaded == expected_download


@pytest.mark.parametrize(
    "workload_params",
    all_zonal_params["read_seq_single_file"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_downloads_one_object(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    """
    this test should use pytest-benchmark,

    target_function should be `download_object`
    setup function should be `my_setup`
    no teardown function for now.

    """
    params, files_names = workload_params

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = loop.run_until_complete(create_client())

    try:
        with monitor() as m:
            benchmark.pedantic(
                target=download_one_object_in_parts,
                iterations=1,
                rounds=params.rounds,
                args=(loop, client, files_names[0], params),
            )
    finally:
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
    publish_benchmark_extra_info(benchmark, params)
    publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )


async def download_chunks_using_mrd_async(client, filename, other_params, chunks):
    # start timer.
    start_time = time.monotonic_ns()

    total_bytes_downloaded = 0
    mrd = AsyncMultiRangeDownloader(client, other_params.bucket_name, filename)
    await mrd.open()
    for offset, size in chunks:
        buffer = BytesIO()
        await mrd.download_ranges([(offset, size, buffer)])
        total_bytes_downloaded += buffer.tell()
    await mrd.close()

    assert total_bytes_downloaded == other_params.file_size_bytes

    # end timer.
    end_time = time.monotonic_ns()
    elapsed_time = end_time - start_time
    logging.debug(f"Time taken to download all chunks: {elapsed_time} ns")
    return elapsed_time / 1_000_000_000


def download_chunks_using_mrd(loop, client, filename, other_params, chunks):
    return loop.run_until_complete(
        download_chunks_using_mrd_async(client, filename, other_params, chunks)
    )


def download_chunks_using_json(_, json_client, filename, other_params, chunks):
    bucket = json_client.bucket(other_params.bucket_name)
    blob = bucket.blob(filename)
    start_time = time.monotonic_ns()
    for offset, size in chunks:
        _ = blob.download_as_bytes(start=offset, end=offset + size)
    return (time.monotonic_ns() - start_time) / 1_000_000_000


@pytest.mark.parametrize(
    "workload_params",
    all_zonal_params["read_rand"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_downloads_single_thread_single_coro(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    """
    1. create chunks based on the object size and chunk_size. [(start_byte, min(chunk_size, remaining_size))]
    2. Pass the list of chunks to `download_chunks_using_mrd` for zonal bucket
                                   `download_chunks_using_json` for regional bucket.
        above function are target methods.
    3. benchmark target method, using benchmark.pedantic



    """
    params, files_names = workload_params

    object_size = params.file_size_bytes
    chunk_size = params.chunk_size_bytes
    chunks = []
    for offset in range(0, object_size, chunk_size):
        size = min(chunk_size, object_size - offset)
        chunks.append((offset, size))

    if params.pattern == "rand":
        logging.info("randomizing chunks")
        random.shuffle(chunks)

    if params.bucket_type == "zonal":
        logging.info("bucket type zonal")
        target_func = download_chunks_using_mrd
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = loop.run_until_complete(create_client())
    else:
        logging.info("bucket type regional")
        target_func = download_chunks_using_json
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
                    chunks,
                ),
            )
            print("type of output", type(output_times), output_times)
    finally:
        if loop is not None:
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()
    publish_benchmark_extra_info(benchmark, params, true_times=output_times)
    publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )


@pytest.mark.parametrize(
    "workload_params",
    all_zonal_params["read_seq_multi_process_single_file"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_downloads_one_object_mp(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    """
    benchmarks download_one_object_in_mn_parts

    """
    params, files_names = workload_params

    with monitor() as m:
        benchmark.pedantic(
            target=download_one_object_in_mn_parts,
            iterations=1,
            rounds=params.rounds,
            args=(files_names[0], params),
        )

    publish_benchmark_extra_info(benchmark, params)
    publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )


@pytest.mark.parametrize(
    "workload_params",
    all_zonal_params["read_seq_multi_process"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_downloads_mn_objects_m_process_n_coros(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    """
    benchmarks for downloads_mn_objects using m_process and n_coros

    """
    params, files_names = workload_params

    with monitor() as m:
        benchmark.pedantic(
            target=download_mn_objects_using_m_process_n_coros,
            iterations=1,
            rounds=params.rounds,
            args=(files_names, params),
        )

    publish_benchmark_extra_info(benchmark, params)
    publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )


@pytest.mark.parametrize(
    "workload_params",
    all_zonal_params["read_rand"],
    indirect=True,
    ids=lambda p: p.name,
)
def test_downloads_mn_objects_m_process_n_coros_random(
    benchmark, storage_client, blobs_to_delete, monitor, workload_params
):
    """
    benchmarks for downloads_mn_objects using m_process and n_coros

    """
    params, files_names = workload_params

    with monitor() as m:
        benchmark.pedantic(
            target=download_mn_objects_using_m_process_n_coros_random,
            iterations=1,
            rounds=params.rounds,
            args=(files_names, params),
        )

    publish_benchmark_extra_info(benchmark, params)
    publish_resource_metrics(benchmark, m)

    blobs_to_delete.extend(
        storage_client.bucket(params.bucket_name).blob(f) for f in files_names
    )
