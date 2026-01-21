# py standard imports
import os
from io import BytesIO

# current library imports
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import (
    AsyncMultiRangeDownloader,
)

# TODO: replace this with a fixture once zonal bucket creation / deletion
# is supported in grpc client or json client client.
_ZONAL_BUCKET = 'chandrasiri-rs'
_BYTES_TO_UPLOAD = b"dummy_bytes_to_write_read_and_delete_appendable_object"


async def mrd_open_with_read_handle(appendable_object):
    grpc_client = AsyncGrpcClient(attempt_direct_path=True).grpc_client

    mrd = AsyncMultiRangeDownloader(grpc_client, _ZONAL_BUCKET, appendable_object)
    await mrd.open()
    read_handle = mrd.read_handle
    await mrd.close()

    # Open a new MRD using the `read_handle` obtained above
    new_mrd = AsyncMultiRangeDownloader(
        grpc_client, _ZONAL_BUCKET, appendable_object, read_handle=read_handle
    )
    await new_mrd.open()
    # persisted_size not set when opened with read_handle
    assert new_mrd.persisted_size is None
    buffer = BytesIO()
    await new_mrd.download_ranges([(0, 0, buffer)])
    await new_mrd.close()
    assert buffer.getvalue() == _BYTES_TO_UPLOAD

if __name__ == "__main__":
    import asyncio
    asyncio.run(mrd_open_with_read_handle('read_handle_123'))
    
