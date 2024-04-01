import json
import logging
import random

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

def download_description(path):
	"""Download the given description from the bucket."""
	bucket = storage_client.bucket(BUCKET_NAME)
	blob = bucket.blob(path)
	return json.loads(blob.download_as_text())

def download_random_movie():
	"""Download a random description from the bucket."""
	blobs = storage_client.list_blobs(BUCKET_NAME, match_glob="movies/**.json")
	selected_blob = random.choice(list(blobs))
	return json.loads(selected_blob.download_as_text())

def fetch_all_movies():
	"""Create a mapping of unique movie names to their public urls."""
	blobs = storage_client.list_blobs(BUCKET_NAME, match_glob="movies/**.json")
	# Sort by movie name
	descriptions = sorted(blobs, key=lambda b: b.name.split("/")[-2])
	
	# The same movie may appear in multiple date prefixes. Return a mapping
	# of unique movies. 
	return { b.name.split("/")[-2]: b.name for b in descriptions }
