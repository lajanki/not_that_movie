import json
import logging
from datetime import date

from googletrans import Translator, LANGUAGES

from jobs import (
	ENV,
	create_image,
	gcs_utils,
	utils,
	document_extract,
)


logger = logging.getLogger(__name__)
translator = Translator()


BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/html"

async def batch_translate_and_upload(batch_size, k=2):
	"""Translate a random sample of titles and store results to
	Cloud Storage bucket.
	Args:
		batch_size (int): number of translations to generate
		k (int): number of intermediary languages to use
	"""
	titles = utils.select_weighted_list_of_movie_names(batch_size)
	for url_title in titles:
		logger.info("##%s", url_title)
		logger.info("%s/%s", BASE_URL, url_title)

		soup = document_extract.make_soup(url_title)
		if not soup.select("#Plot"):
			logger.error("https://en.wikipedia.org/wiki/%s doesn't apper to be a valid movie article.", url_title)
			continue

		title = document_extract.format_title(url_title)
			
		# Generate and upload a poster image
		prompt = f"A poster to a fictional movie titled '{title}'"
		logger.info("Image prompt: %s", prompt)
		img_blob = gcs_utils.upload(
			create_image.create_image_by_env[ENV](prompt),
			f"movies/{date.today().strftime('%Y-%m-%d')}/{title}/image.png",
			content_type="image/png"
		)

		# Generate a translation
		sections_to_translate = {
			"title": title,
			"plot": document_extract.get_plot(soup),
			"cast": document_extract.get_cast(soup),
			"infobox": utils.dict_to_newline_string(document_extract.get_movie_infobox(soup))
		}
		result = await generate_translation(sections_to_translate, k)

		# Add the original titles
		result["metadata"].update({
			"original_title": title,
			"url_title": url_title
		})

		# Add a (public) link to the related image
		result["img"] = img_blob.public_url

		gcs_utils.upload(
			json.dumps(result),
			f"movies/{date.today().strftime('%Y-%m-%d')}/{title}/description.json"
		)

async def generate_translation(sections_to_translate, k, target_language="en"):
	"""Translate a single Wikipedia movie article.
	Args:
		sections_to_translate (dict): A mapping of sections fron the original article to translate
		k (int): number of intermediary languages to translate to
		target_language (str): language code for the final output language
	Return:
		A dict of the trasnalted section, similar to the input
	"""
	translated_sections = {}
	chain = utils.generate_language_chain(k, source_language="en", target_language=target_language)
	language_names = " => ".join([LANGUAGES[code] for code in chain])
	logger.info("Languages to use %s", language_names)

	for idx, section in enumerate(sections_to_translate):
		logger.info("Translating %s (%d of %d)", section, idx+1, len(sections_to_translate))

		text = sections_to_translate[section]
		if len(text) > 5000:
			logger.info("%s length=%d, truncating to 5000 characters", section, len(text))
			text = text[:5000]
		
		for previous, current in zip(chain, chain[1:]):
			translated = await translator.translate(text, src=previous, dest=current)
			text = translated.text
		
		text = utils.cleanup_translation(text)
		translated_sections[section] = text

	# Convert infobox back to a dict
	translated_sections["infobox"] = utils.newline_string_to_dict(translated_sections["infobox"])

	# Move translated title to a dedicated metadata section
	translated_sections["metadata"] = {
		"title": translated_sections.pop("title").title()
	}
	
	return translated_sections
