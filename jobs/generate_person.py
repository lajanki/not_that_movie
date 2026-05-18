import logging
import random
from datetime import date

from jobs import (
	document_extract,
	env_config,
	generate_movie,
	gcs_utils,
	utils,
	ENV,
	BASE,
)
from jobs.models import ArticleData


logger = logging.getLogger(__name__)
create_image = env_config.create_image_[ENV]


async def batch_translate_and_upload(batch_size: int, k: int = 2) -> None:
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
			create_image(prompt),
			f"people/{date.today().strftime('%Y-%m-%d')}/{title}/image.png",
			content_type="image/png"
		)

		article_data = ArticleData(
			title=title,
			content={
				"description": document_extract.get_description(soup),
			},
			infobox=document_extract.get_person_infobox(soup),
			metadata={
				"original_title": title,
				"url_title": url_title
			},
			img={
				"prompt": prompt,
				"url": img_blob.public_url
			}
		)

		result = await generate_movie.generate_translation(article_data, k)
		
		if not utils.is_mostly_ascii(result.content["description"]):
			logger.warning("Rejected translation: output does not appear to be English.")
			continue

		gcs_utils.upload(
			result.model_dump_json(),
			f"people/{date.today().strftime('%Y-%m-%d')}/{title}/description.json"
		)

def get_people_list() -> list[str]:
	"""Get a list of people from people.txt."""
	with open(BASE / "data" / "people.txt") as f:
		people = [
			row.strip()
			for row in f.readlines()
			if row.strip() and not row.startswith("#")
		]

	return people

def get_person_portrait_prompt(category: str) -> str:
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
