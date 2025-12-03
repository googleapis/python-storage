from google.cloud import storage

gcs = storage.Client()
bucket = gcs.bucket("chandrasiri-us-west1-hns-soft-del")
# print(bucket.name)
blob = bucket.blob("test/blob.csv")
blob.upload_from_string("")
print("Uploaded blob:", blob.name)
bucket.move_blob(blob, new_name="test/blob2.csv")
