import asyncio
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)
from io import BytesIO
import os
import time
import uuid


async def write_appendable_object_and_read_using_mrd():

    client = AsyncGrpcClient().grpc_client
    bucket_name = "chandrasiri-rs"
    object_name = f"11Dec.100.3"
    # data_to_append = os.urandom(10 * 1024 * 1024 + 1)  # 10 MiB + 1 of random data

    # # 1. Write to an appendable object
    # writer = AsyncAppendableObjectWriter(client, bucket_name, object_name)
    # await writer.open()
    # print(f"Opened writer for object: {object_name}, generation: {writer.generation}")

    # start_write_time = time.monotonic_ns()
    # await writer.append(data_to_append)
    # end_write_time = time.monotonic_ns()
    # print(
    #     f"Appended {len(data_to_append)} bytes in "
    #     f"{(end_write_time - start_write_time) / 1_000_000:.2f} ms"
    # )

    # await writer.close(finalize_on_close=False)

    # 2. Read the object using AsyncMultiRangeDownloader
    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name)
    await mrd.open()
    print(f"Opened downloader for object: {object_name}")

    # Define a single range to download the entire object
    output_buffer = BytesIO()
    download_ranges = [(0, 100*1000*1000, output_buffer)]

    await mrd.download_ranges(download_ranges)
    for _, buffer in mrd._read_id_to_writable_buffer_dict.items():
        print("*" * 80)
        print(buffer.getbuffer().nbytes)
        print("*" * 80)
    await mrd.close()


if __name__ == "__main__":
    asyncio.run(write_appendable_object_and_read_using_mrd())
