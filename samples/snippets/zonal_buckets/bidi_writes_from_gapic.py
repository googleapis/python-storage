"""


async def open_file('file_name')


async def append_to_file('file_name')


async def close('')

"""

import os
import time
import asyncio
from google.cloud import _storage_v2 as storage_v2
import argparse

# from async_get_object_metadata import get_object

BUCKET_NAME = "chandrasiri-rs"
BUCKET_FULLNAME = f"projects/_/buckets/{BUCKET_NAME}"


def generate_random_bytes_os_urandom(length_mib):
    """
    Generates cryptographically secure random bytes of a specified length in MiB.

    Args:
        length_mib (int): The desired length of random bytes in MiB (Megabytes).

    Returns:
        bytes: A bytes object containing the random bytes.
    """
    length_bytes = length_mib * 1024 * 1024  # Convert MiB to bytes
    random_bytes = os.urandom(length_bytes)
    return random_bytes


def create_async_client():
    transport_cls = storage_v2.StorageClient.get_transport_class(label="grpc_asyncio")
    channel = transport_cls.create_channel(attempt_direct_path=True)
    transport = transport_cls(channel=channel)
    async_client = storage_v2.StorageAsyncClient(transport=transport)

    return async_client


async def open_file(filename, client):
    first_request = storage_v2.BidiWriteObjectRequest(
        write_object_spec=storage_v2.WriteObjectSpec(
            resource=storage_v2.Object(name=filename, bucket=BUCKET_FULLNAME),
            appendable=True,
        ),
    )

    def request_generator():
        for request in [first_request]:
            yield request

    req_param = f"bucket={BUCKET_FULLNAME}"
    response_stream = await client.bidi_write_object(
        requests=request_generator(),
        metadata=(
            ("x-goog-request-params", req_param),
            ("x-goog-api-client", "gcloud-python-local/3.8.0"),
        ),
    )
    generation = None
    write_handle = None
    count = 0
    async for response in response_stream:
        # print("stream count:", count, "*" * 20)
        # print(response)
        # print("time elapsed", time_elapsed)
        # print("stream count:", count, "*" * 20)
        if response.resource is not None and (generation is None):

            generation = response.resource.generation

            # print("genration = ", generation)
        if response.write_handle is not None and (write_handle is None):
            write_handle = response.write_handle.handle
            # print("write_handle = ", write_handle)

        # if
    return generation, write_handle


async def append_to_file(filename, generation, client, data, write_handle=None):
    # print("generation in append ", generation)

    def request_generator_for_append():
        # current  persisted size of object
        # start_offset = 1 * 1024 * 1024
        start_offset = 0
        curr_byte = 0
        total_bytes = len(data)
        chunk_size = 2 * 1024 * 1024
        stream_count = 0
        if total_bytes == 0:
            # print("@@" * 20)
            yield storage_v2.BidiWriteObjectRequest(
                append_object_spec=storage_v2.AppendObjectSpec(
                    bucket=BUCKET_FULLNAME,
                    object=filename,
                    generation=generation,
                ),
                checksummed_data=storage_v2.ChecksummedData(content=b""),
                write_offset=curr_byte + start_offset,
                # flush=True,
                # state_lookup=True,
                # finish_write=True,
            )
        while curr_byte < total_bytes:
            curr_chunk_size = min(chunk_size, total_bytes - curr_byte)
            chunked_data = data[curr_byte : curr_byte + curr_chunk_size]
            # create req
            if stream_count == 0:
                bidi_request = storage_v2.BidiWriteObjectRequest(
                    append_object_spec=storage_v2.AppendObjectSpec(
                        bucket=BUCKET_FULLNAME,
                        object=filename,
                        generation=generation,
                        write_handle=storage_v2.BidiWriteHandle(handle=write_handle),
                    ),
                    checksummed_data=storage_v2.ChecksummedData(content=chunked_data),
                    write_offset=curr_byte + start_offset,
                )
            else:
                bidi_request = storage_v2.BidiWriteObjectRequest(
                    checksummed_data=storage_v2.ChecksummedData(content=chunked_data),
                    write_offset=curr_byte + start_offset,
                )

            if curr_byte + chunk_size >= total_bytes:
                bidi_request.flush = True
                bidi_request.state_lookup = True

            # yield req
            yield bidi_request
            curr_byte += curr_chunk_size
            stream_count += 1

    req_param = f"bucket={BUCKET_FULLNAME}"
    append_stream = await client.bidi_write_object(
        requests=request_generator_for_append(),
        metadata=(("x-goog-request-params", req_param),),
    )
    count = 0
    prev_time = time.monotonic_ns()
    total_time = 0
    async for response in append_stream:
        end_time = time.monotonic_ns()
        elapsed_time = end_time - prev_time
        total_time += elapsed_time
        print(f"Response count: {count}:", response)
        count += 1


async def main():
    data = generate_random_bytes_os_urandom(10)
    storage_async_client = create_async_client()

    generation = None
    write_handle = None

    filename = args.filename
    # if not args.skip_open:
    generation, write_handle = await open_file(filename, storage_async_client)
    print("Opend file for writing, gen:", generation)
    # if not args.skip_append:
    # if generation is None:
    #     print("generation is none requesting it")
    #     object_metadata = await get_object(
    #         bucket_fullname=BUCKET_FULLNAME, object_name=filename
    #     )
    #     generation = object_metadata.generation
    # print("generation is ", generation)
    # await append_to_file(filename, generation, storage_async_client, data, write_handle)


parser = argparse.ArgumentParser()
parser.add_argument("--filename", required=True)
parser.add_argument("--skip_open", action="store_true")
parser.add_argument("--skip_append", action="store_true")
args = parser.parse_args()
# print(args.skip_open, args.skip_append)
# print("yo")
asyncio.run(main())
