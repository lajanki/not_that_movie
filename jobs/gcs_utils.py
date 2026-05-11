import json
import logging
import random

from google.cloud import storage
from jobs import ENV
from jobs.constants import ContentType
from jobs.env_config import bucket_map

BUCKET_NAME = bucket_map[ENV]
storage_client = storage.Client()

logger = logging.getLogger(__name__)


def upload(contents, destination_blob_name, content_type="text/plain"):
	"""Uploads a file to the data bucket.
	Args:
		contents (str or bytes): the content to upload
		destination_blob_name (str): the path to upload the content to in the bucket
		content_type (str): the content type of the uploaded content
	Return:
		The blob object of the uploaded content.
	"""
	bucket = storage_client.bucket(BUCKET_NAME)
	blob = bucket.blob(destination_blob_name)

	logger.info("Uploading to gs://%s/%s", BUCKET_NAME, destination_blob_name)
	blob.upload_from_string(contents, content_type=content_type)
	return blob

def download_description(path):
	"""Download the given description from the bucket.

	Args:
		path (str): the path to the object in the bucket
	Return:
		The content of the object as a dict.
	"""
	bucket = storage_client.bucket(BUCKET_NAME)
	blob = bucket.blob(path)
	return json.loads(blob.download_as_text())

def download_random_content(content_type):
	"""Download a random description from the bucket.
	Either a movie or a person.

	Args:
		content_type (str): the content type to fetch, one of ContentType Enum.
	Return:
		The content of the object as a dict.
	"""
	# Map content type to bucket prefix
	prefix_map = {
		ContentType.PERSON.name: "people",
		ContentType.MOVIE.name: "movies"
	}
	item_prefix = prefix_map[content_type]

	blobs = storage_client.list_blobs(BUCKET_NAME, match_glob=f"{item_prefix}/**.json")
	selected_blob = random.choice(list(blobs))
	return json.loads(selected_blob.download_as_text())

def fetch_all_movies():
	"""Fetch a list of all movies currently in the bucket.

	Return:
		A mapping of unique movie names to their public urls.
	"""
	blobs = storage_client.list_blobs(BUCKET_NAME, match_glob="movies/**.json")
	# Sort by movie name
	descriptions = sorted(blobs, key=lambda b: b.name.split("/")[-2])
	
	# The same movie may appear in multiple date prefixes. Return a mapping
	# of unique movies. 
	return { b.name.split("/")[-2]: b.name for b in descriptions }
