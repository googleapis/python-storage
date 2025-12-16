# test_retry.py (Minimal Diagnostic Version)

import asyncio
import docker
import time
import uuid

from google.api_core import exceptions
from google.cloud import _storage_v2 as storage_v2
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient

# --- Configuration ---
TESTBENCH_IMAGE = "gcr.io/cloud-devrel-public-resources/storage-testbench:latest"
PROJECT_NUMBER = "30215529953"

async def main():
    docker_client = docker.from_env()
    container = None
    bucket_name = f"minimal-test-bucket-{uuid.uuid4().hex[:8]}"
    object_name = "minimal-object"

    print("--- Minimal Write/Read Integration Test ---")

    try:
        # 1. Start Testbench
        print("Starting storage-testbench container...")
        container = docker_client.containers.run(
            TESTBENCH_IMAGE, detach=True, ports={"9000/tcp": 9000}
        )
        time.sleep(3)
        print(f"Testbench container {container.short_id} is running.")

        # 2. Create Client
        client_options = {"api_endpoint": "localhost:9000"}
        grpc_client = AsyncGrpcClient(client_options=client_options)
        gapic_client = grpc_client._grpc_client

        # 3. Create Bucket
        print(f"Creating test bucket gs://{bucket_name}...")
        bucket_resource = storage_v2.Bucket(project=f"projects/{PROJECT_NUMBER}")
        create_bucket_request = storage_v2.CreateBucketRequest(
            parent="projects/_", bucket_id=bucket_name, bucket=bucket_resource
        )
        await gapic_client.create_bucket(request=create_bucket_request)
        print("Bucket created successfully.")

        # 4. Write Object
        print(f"Creating test object gs://{bucket_name}/{object_name}...")
        write_spec = storage_v2.WriteObjectSpec(
            resource=storage_v2.Object(bucket=f"projects/_/buckets/{bucket_name}", name=object_name)
        )

        async def write_request_generator():
            yield storage_v2.WriteObjectRequest(write_object_spec=write_spec)
            yield storage_v2.WriteObjectRequest(
                checksummed_data={"content": b"test data"},
                finish_write=True
            )

        # CRITICAL: Capture and inspect the response from the write operation.
        write_response = await gapic_client.write_object(requests=write_request_generator())
        print(f"Write operation completed. Response from server: {write_response}")

        # The `write_object` RPC only returns a resource on the *final* message of a stream.
        # If this is not present, the object was not finalized correctly.
        if not write_response.resource:
            print("\n!!! CRITICAL FAILURE: The write response did not contain a finalized resource. The object may not have been created correctly. !!!")
            raise ValueError("Object creation failed silently on the server.")

        print("Test object appears to be finalized successfully.")

        # 5. Attempt to Read the Object Metadata
        print("\nAttempting to read the object's metadata back immediately...")
        get_object_request = storage_v2.GetObjectRequest(
            bucket=f"projects/_/buckets/{bucket_name}",
            object=object_name,
        )
        read_object = await gapic_client.get_object(request=get_object_request)
        print("--- SUCCESS: Object read back successfully. ---")
        print(f"Read object metadata: {read_object}")

    except Exception as e:
        import traceback
        print("\n!!! TEST FAILED. The original error is below: !!!")
        traceback.print_exc()
    finally:
        # 6. Cleanup
        if container:
            print("Stopping and removing testbench container...")
            container.stop()
            container.remove()
            print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())
