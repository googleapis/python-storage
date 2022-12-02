# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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

from google.cloud.storage import Client, transfer_manager


def upload_many_blobs_with_transfer_manager(bucket_name, filenames, source_directory=""):
    """Upload every file in a list to a bucket, concurrently in a thread pool.

    Each blob name is derived from the filename, not including the `root`
    parameter. For complete control of the blob name for each file (and other
    aspects of individual blob metadata), use transfer_manager.upload_many()
    instead.
    """

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # A list (or other iterable) of filenames to upload.
    # filenames = ["file_1.txt", "file_2.txt"]

    # The directory on your computer that is the root of all of the files in the
    # list of filenames. This string is prepended (with os.path.join()) to each
    # filename to get the full path to the file. Relative paths and absolute
    # paths are both accepted. This string is not included in the name of the
    # uploaded blob; it is only used to find the source files. An empty string
    # means "the current working directory". Note that this parameter allows
    # directory traversal (e.g. "/", "../") and is not intended for unsanitized
    # end user input.
    # source_directory=""

    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)

    results = transfer_manager.upload_many_from_filenames(bucket, filenames, source_directory=source_directory)

    for name, result in zip(filenames, results):
        # The results list is either `None` or an exception for each filename in
        # the input list, in order.

        if isinstance(result, Exception):
            print("Failed to upload {} due to exception: {}".format(name, result))
        else:
            print("Uploaded {} to {}.".format(name, bucket.name))


def download_all_blobs_with_transfer_manager(bucket_name, destination_directory=""):
    """Download all of the blobs in a bucket, concurrently in a thread pool.

    The filename of each blob once downloaded is derived from the blob name and
    the `destination_directory `parameter. For complete control of the filename
    of each blob, use transfer_manager.download_many() instead.

    Directories will be created automatically as needed, for instance to
    accommodate blob names that include slashes.
    """

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The directory on your computer to which to download all of the files. This
    # string is prepended (with os.path.join()) to the name of each blob to form
    # the full path. Relative paths and absolute paths are both accepted. An
    # empty string means "the current working directory". Note that this
    # parameter allows accepts directory traversal ("../" etc.) and is not
    # intended for unsanitized end user input.
    # destination_directory = ""

    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)

    blob_names = [blob.name for blob in bucket.list_blobs()]

    results = transfer_manager.download_many_to_path(
        bucket, blob_names, destination_directory=destination_directory
    )

    for name, result in zip(blob_names, results):
        # The results list is either `None` or an exception for each blob in
        # the input list, in order.

        if isinstance(result, Exception):
            print("Failed to download {} due to exception: {}".format(name, result))
        else:
            print("Downloaded {} to {}.".format(name, destination_directory + name))


def download_blob_chunks_concurrently_with_transfer_manager(
    bucket_name, blob_name, local_filename, chunk_size=200 * 1024 * 1024
):
    """Download a single blob, in chunks, concurrently in a thread pool.

    This is intended for use with very large blobs."""

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The name of the blob to download.
    # blob_name = "your-blob.txt"

    # The filename (or path) on your computer to which to download the blob.
    # local_filename = "your-file.txt"

    # The size of each chunk. For instance, if the chunk size is 200 megabytes,
    # a 1.6 gigabyte file would be downloaded in eight pieces concurrently.
    # chunk_size = 200 * 1024 * 1024  # 200 MiB.

    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(blob_name)

    # Open the local file in binary write mode.
    local_file = open(local_filename, "wb")

    # Unlike other transfer manager functions, which handle multiple files and
    # return exceptions in a list, this function will simply raise any exception
    # it encounters, and has no return value.
    transfer_manager.download_chunks_concurrently_to_file(
        blob, local_file, chunk_size=chunk_size
    )

    # If we've gotten this far, it must have been successful.

    number_of_chunks = -(blob.size // -chunk_size)  # Ceiling division
    print(
        "Downloaded {} to {} in {} chunk(s).".format(
            blob_name, local_file.name, number_of_chunks
        )
    )
