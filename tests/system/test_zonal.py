from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_appendable_object_writer import (
    AsyncAppendableObjectWriter,
)
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)
import uuid
from io import BytesIO

import pytest


@pytest.mark.asyncio
async def test_zonal_create_object_and_read():

    bucket_name = "gcsfs-cloudbuild-zonal-bucket"
    # bucket_name = "chandrasiri-rs"
    bytes_to_upload = b"These_are_some_dummy_bytes_for_to_test_zb_with_cloud_build"
    object_name = f"chandrasiri-zb-{str(uuid.uuid4())}"
    grpc_client = AsyncGrpcClient().grpc_client
    writer = AsyncAppendableObjectWriter(grpc_client, bucket_name, object_name)
    await writer.open()
    await writer.append(bytes_to_upload)
    object_metadata = await writer.close(finalize_on_close=True)
    assert object_metadata.size == len(bytes_to_upload)

    mrd = AsyncMultiRangeDownloader(grpc_client, bucket_name, object_name)
    buffer = BytesIO()
    await mrd.open()
    await mrd.download_ranges([(0, 0, buffer)])
    await mrd.close()
    assert buffer.getvalue() == bytes_to_upload


# if __name__ == "__main__":
#     asyncio.run(test_zonal_create_object_and_read())
