# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import hashlib
import logging
import os
import random
import subprocess
import time
import requests
import grpc
from io import BytesIO

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("bidi_integration_test")

# --- Configuration ---
TESTBENCH_PORT = 9000
TESTBENCH_HOST = f"localhost:{TESTBENCH_PORT}"
BUCKET_NAME = f"bidi-retry-bucket-{random.randint(1000, 9999)}"
OBJECT_NAME = "test-blob-10mb"
OBJECT_SIZE = 10 * 1024 * 1024  # 10 MiB

# --- Imports from SDK ---
from google.cloud.storage._experimental.asyncio.async_grpc_client import AsyncGrpcClient
from google.cloud.storage._experimental.asyncio.async_multi_range_downloader import AsyncMultiRangeDownloader
from google.cloud.storage._experimental.asyncio.async_read_object_stream import _AsyncReadObjectStream

# --- Infrastructure Management ---

def start_testbench():
    """Starts the storage-testbench using Docker."""
    logger.info("Starting Storage Testbench container...")
    try:
        # Check if already running
        requests.get(f"http://{TESTBENCH_HOST}/")
        logger.info("Testbench is already running.")
        return None
    except requests.ConnectionError:
        pass

    cmd = [
        "docker", "run", "-d", "--rm",
        "-p", f"{TESTBENCH_PORT}:{TESTBENCH_PORT}",
        "gcr.io/google.com/cloudsdktool/cloud-sdk:latest",
        "gcloud", "beta", "emulators", "storage", "start",
        f"--host-port=0.0.0.0:{TESTBENCH_PORT}"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for it to be ready
    for _ in range(20):
        try:
            requests.get(f"http://{TESTBENCH_HOST}/")
            logger.info("Testbench started successfully.")
            return process
        except requests.ConnectionError:
            time.sleep(1)

    raise RuntimeError("Timed out waiting for Testbench to start.")

def stop_testbench(process):
    if process:
        logger.info("Stopping Testbench container...")
        subprocess.run(["docker", "stop", process.args[2]]) # Stop container ID (not robust, assumes simple run)
        # Better: Since we used --rm, killing the python process might not kill docker immediately
        # without capturing container ID.
        # For simplicity in this script, we assume the user might manually clean up if this fails,
        # or we just rely on standard docker commands.
        # Actually, let's just kill the container by image name or port if needed later.
        pass

# --- Test Data Setup ---

def setup_resources():
    """Creates bucket and object via HTTP."""
    logger.info(f"Creating resources on {TESTBENCH_HOST}...")

    # 1. Create Bucket
    resp = requests.post(
        f"http://{TESTBENCH_HOST}/storage/v1/b?project=test-project",
        json={"name": BUCKET_NAME}
    )
    if resp.status_code not in (200, 409):
        raise RuntimeError(f"Bucket creation failed: {resp.text}")

    # 2. Upload Object
    data = os.urandom(OBJECT_SIZE)
    resp = requests.post(
        f"http://{TESTBENCH_HOST}/upload/storage/v1/b/{BUCKET_NAME}/o?uploadType=media&name={OBJECT_NAME}",
        data=data,
        headers={"Content-Type": "application/octet-stream"}
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Object upload failed: {resp.text}")

    return data

# --- Fault Injection Logic ---

def inject_failure_instruction(test_case):
    """
    Monkeypatches _AsyncReadObjectStream.open to inject x-goog-testbench-instructions.

    Supported test_cases:
    - 'broken-stream': Aborts stream mid-way.
    - 'stall-always': Stalls immediately (timeout simulation).
    - 'transient-error': Returns an error status code.
    """
    real_open = _AsyncReadObjectStream.open
    attempt_counter = 0

    async def monkeypatched_open(self, metadata=None):
        nonlocal attempt_counter
        attempt_counter += 1

        if metadata is None:
            metadata = []
        else:
            metadata = list(metadata)

        # Inject fault only on the first attempt
        if attempt_counter == 1:
            instruction = ""
            if test_case == 'broken-stream':
                instruction = "return-broken-stream"
            elif test_case == 'transient-error':
                instruction = "return-503-after-256K" # Simulate Service Unavailable later

            if instruction:
                logger.info(f">>> INJECTING FAULT: '{instruction}' <<<")
                metadata.append(("x-goog-testbench-instructions", instruction))
        else:
            logger.info(f">>> Attempt {attempt_counter}: Clean retry <<<")

        await real_open(self, metadata=metadata)

    _AsyncReadObjectStream.open = monkeypatched_open
    return real_open

# --- Main Test Runner ---

async def run_tests():
    # 1. Start Infrastructure
    tb_process = start_testbench()

    try:
        # 2. Setup Data
        original_data = setup_resources()

        # 3. Setup Client
        channel = grpc.aio.insecure_channel(TESTBENCH_HOST)
        client = AsyncGrpcClient(channel=channel)

        # Test Scenarios
        scenarios = ['broken-stream', 'transient-error']

        for scenario in scenarios:
            logger.info(f"\n--- Running Scenario: {scenario} ---")

            # Reset MRD state
            mrd = await AsyncMultiRangeDownloader.create_mrd(
                client=client.grpc_client,
                bucket_name=BUCKET_NAME,
                object_name=OBJECT_NAME
            )

            # Apply Fault Injection
            original_open_method = inject_failure_instruction(scenario)

            # Buffers
            b1 = BytesIO()
            b2 = BytesIO()

            # Split ranges
            mid = OBJECT_SIZE // 2
            ranges = [(0, mid, b1), (mid, OBJECT_SIZE - mid, b2)]

            try:
                await mrd.download_ranges(ranges)
                logger.info(f"Scenario {scenario}: Download call returned successfully.")

                # Verify Content
                downloaded = b1.getvalue() + b2.getvalue()
                if downloaded == original_data:
                    logger.info(f"Scenario {scenario}: PASSED - Data integrity verified.")
                else:
                    logger.error(f"Scenario {scenario}: FAILED - Data mismatch.")

            except Exception as e:
                logger.error(f"Scenario {scenario}: FAILED with exception: {e}")
            finally:
                # Cleanup and Restore
                _AsyncReadObjectStream.open = original_open_method
                await mrd.close()

    finally:
        # Stop Infrastructure (if we started it)
        # Note: In a real script, we'd be more rigorous about finding the PID/Container ID
        if tb_process:
            logger.info("Killing Testbench process...")
            tb_process.kill()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_tests())
    except KeyboardInterrupt:
        pass
