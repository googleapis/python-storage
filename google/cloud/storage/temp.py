import random
from absl import app
from google.cloud import storage
import tink
from tink import secret_key_access
from tink import streaming_aead
import os

streaming_aead.register()

SMALL_CHUNK_SIZE = 256 * 1024  # smallest chunk size allowed.
BLOCK_SIZE = 1024  # 1kb
BLOCK_NUM = 40_000
BUCKET_NAME = "pulkitaggarwal-bucket-sdk"
BLOB_NAME = "temp2"
HEADER = b"start"
FOOTER = b"end"

_streaming_aead_keyset = """
  {"primaryKeyId":506873687,
    "key":[
      {
        "keyData":{
            "typeUrl":"type.googleapis.com/google.crypto.tink.AesGcmHkdfStreamingKey",
            "value":"EgcIgCAQEBgDGhC1lq3VdCCOjEm9A/g/TqPo",
            "keyMaterialType":"SYMMETRIC"
          },
        "status":"ENABLED",
        "keyId":506873687,
        "outputPrefixType":"RAW"
      }
    ]
  }
"""


def get_primitive() -> streaming_aead.StreamingAead:
    handle = tink.json_proto_keyset_format.parse(
        _streaming_aead_keyset, secret_key_access.TOKEN
    )
    primitive = handle.primitive(streaming_aead.StreamingAead)
    return primitive


def main(argv):
    del argv  # Unused.
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(BLOB_NAME, chunk_size=SMALL_CHUNK_SIZE)
    output_stream = blob.open("wb", ignore_flush=True)

    output_stream.write(HEADER)
    for _ in range(BLOCK_NUM):
        rand_block = os.urandom(BLOCK_SIZE)
        written = output_stream.write(rand_block)
        if written > len(rand_block):
            raise ValueError(
                "written is larger than expected: written = %d, len(rand_block)"
                " = %d" % (written, len(rand_block))
            )
    output_stream.write(FOOTER)
    output_stream.close()


if __name__ == "__main__":
    app.run(main)
