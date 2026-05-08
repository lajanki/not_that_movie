import base64
from io import BytesIO
import logging
import os

from openai import OpenAI
from PIL import Image

from jobs import BASE


logger = logging.getLogger(__name__)

def create_image(prompt):
	"""Generate an image using OpenAI image model."""
	api_key = os.environ["OPENAI_API_KEY"]
	client = OpenAI(api_key=api_key)

	img = client.images.generate(
		model="gpt-image-1-mini",
		prompt=prompt,
		n=1,
		size="1024x1024",
		quality="low",
	)
	image_bytes = base64.b64decode(img.data[0].b64_json)

	# Resize the image to 512x512 using PIL
	fp = BytesIO(image_bytes)
	image = Image.open(fp)
	image = image.resize((512, 512), Image.LANCZOS)

	fp = BytesIO()
	image.save(fp, format="PNG")

	fp.seek(0)
	return fp.getvalue()

def get_template_image(*args):
	"""Get template image content."""
	logger.warning("Using default poster image")
	with open(BASE / "img" / "default_poster.png", "rb") as f:
		return f.read()

create_image_by_env = {
	"prod": create_image,
	"stg": create_image,
	"dev": get_template_image
}
