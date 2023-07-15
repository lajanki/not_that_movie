import base64
import logging

import openai

from src import utils


openai.api_key = utils.get_openai_secret()


def create_image(prompt):
	"""Generate an image using openai DALL-E model."""
	response = openai.Image.create(
		prompt=prompt,
		n=1,
		size="256x256",
		response_format="b64_json"
	)
	image_data = response["data"][0]["b64_json"].encode()

	return base64.b64decode(image_data)

def create_test_image(*args):
	"""Get test image content."""
	logging.info("Using default poster image")
	with open("./static/default_poster.png", "rb") as f:
		return f.read()

create_image_by_env = {
	"prod": create_image,
	"dev": create_test_image
}
