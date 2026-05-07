import json
import logging
import random
from datetime import date

from jobs import (
	document_extract,
	generate_movie,
	utils,
	gcs_utils,
	create_image,
	ENV,
	BASE,
)


logger = logging.getLogger(__name__)


async def batch_translate_and_upload(batch_size, k=2):
	"""Translate a random sample of titles for person articles and store results to
	Cloud Storage bucket.
	Args:
		batch_size (int): number of translations to generate
		k (int): number of intermediary languages to use
	"""
	people_tokens = random.sample(get_people_list(), batch_size)
	for token in people_tokens:
		url_title = token.split(";")[1]
		logger.info("##%s", url_title)
		logger.info("%s/%s", document_extract.BASE_URL, url_title)

		soup = document_extract.make_soup(url_title)
		title = document_extract.format_title(url_title)

		# Generate and upload a poster image
		category = token.split(";")[0]
		prompt = get_person_portrait_prompt(category)
		logger.info("Image prompt: %s", prompt)
		img_blob = gcs_utils.upload(
			create_image.create_image_by_env[ENV](prompt),
			f"people/{date.today().strftime('%Y-%m-%d')}/{title}/image.png",
			content_type="image/png"
		)

		# Generate a translation
		sections_to_translate = {
			"title": title,
			"description": document_extract.get_description(soup),
			"infobox": utils.dict_to_newline_string(document_extract.get_person_infobox(soup))
		}
		result = await generate_movie.generate_translation(sections_to_translate, k)
		
		result["img"] = img_blob.public_url
		result["img_prompt"] = prompt

		result["metadata"].update({
			"original_title": title,
			"url_title": url_title
		})

		gcs_utils.upload(
			json.dumps(result),
			f"people/{date.today().strftime('%Y-%m-%d')}/{title}/description.json"
		)

def get_people_list():
	"""Get a list of people from people.txt."""
	with open(BASE / "data" / "people.txt") as f:
		people = [
			row.strip()
			for row in f.readlines()
			if row.strip() and not row.startswith("#")
		]

	return people

def get_person_portrait_prompt(category):
	"""Select a random prompt for a person portrait image.
	Args:
		category (str): the category of prompts to choose from: actor|director
	"""
	with open(BASE / "data" / "portrait_prompts.txt") as f:
		prompts = [
			row.split(";")[1].strip()
			for row in f.readlines()
			if row.strip()
			and not row.startswith("#")
			and row.split(";")[0].strip() == category
		]
	return random.choice(prompts)
