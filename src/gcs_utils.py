import json
import logging
import random
from datetime import date

from google.cloud import storage

from src import ENV


BUCKET_NAME = f"{ENV}_not_that_movie"
storage_client = storage.Client()


def upload(contents, destination_blob_name, content_type="text/plain"):
	"""Uploads a file to the data bucket."""
	bucket = storage_client.bucket(BUCKET_NAME)
	blob = bucket.blob(destination_blob_name)

	logging.info("Uploading to gs://%s/%s", BUCKET_NAME, destination_blob_name)
	blob.upload_from_string(contents, content_type=content_type)
	return blob

def download_random():
	"""Download a random description and image from the bucket.
	Return
		a dict of the json content and the image bytes.
	"""
	blobs = storage_client.list_blobs(BUCKET_NAME)

	# Fetch json description content
	selected_blob = random.choice([ b for b in blobs if b.name.endswith(".json") ])
	description = json.loads(selected_blob.download_as_text())

	return description
