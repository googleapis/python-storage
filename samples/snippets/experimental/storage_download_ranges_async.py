from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
from google.cloud.storage._experimental.asyncio.async_grpc_client import (
    AsyncGrpcClient,
)
from io import BytesIO
import asyncio
import argparse


async def test_mrd(bucket_name, object_name, generation_number=None):
    client = AsyncGrpcClient()._grpc_client

    mrd = AsyncMultiRangeDownloader(client, bucket_name, object_name, generation_number)
    await mrd.open()
    # create buffers.
    # Make sure buffer desitnation has enough space to accomodate bytes requetsed.
    # Buffers could be in-memory or on disk
    my_buff1 = open(f"sample_file_to_write_contents.txt", "wb")
    my_buff2 = BytesIO()
    my_buff3 = BytesIO()
    my_buff4 = BytesIO()
    results_arr, error_obj = await mrd.download_ranges(
        [
            (0, 100, my_buff1),
            (100, 20, my_buff2),
            (200, 123, my_buff3),
            (300, 789, my_buff4),
        ]
    )
    if error_obj:
        print("Error occurred: ")
        print(error_obj)
        print(
            "please issue call to `download_ranges` with updated"
            "`read_ranges` based on diff of (bytes_requested - bytes_written)"
        )

    for result in results_arr:
        print("downloaded bytes", result)

    # close MRD
    await mrd.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, required=True)
    parser.add_argument("--object_name", type=str, required=True)
    parser.add_argument("--generation_number", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(test_mrd(args.bucket_name, args.object_name, args.generation_number))
