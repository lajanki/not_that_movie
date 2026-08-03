from difflib import SequenceMatcher
import logging
from datetime import date
from pathlib import Path

from googletrans import Translator, LANGUAGES

from jobs import (
	ENV,
	env_config,
	gcs_utils,
	utils,
	document_extract,
)
from jobs.models import ArticleData


logger = logging.getLogger(__name__)
translator = Translator()

create_image = env_config.create_image_[ENV]


BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/html"

async def batch_translate_and_upload(batch_size: int, k: int = 2) -> None:
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
			create_image(prompt),
			f"movies/{date.today().strftime('%Y-%m-%d')}/{title}/image.png",
			content_type="image/png"
		)
		
		# Create an ArticleData object for the translation
		plot = document_extract.get_plot(soup)
		article_data = ArticleData(
			title=title,
			content={
				"plot": plot,
				"cast": document_extract.get_cast(soup)
			},
			infobox=document_extract.get_movie_infobox(soup),
			metadata={
				"original_title": title,
				"url_title": url_title
			},
			img={
				"prompt": prompt,
				"url": img_blob.public_url
			}
		)

		result = await generate_translation(article_data, k)

		# Reject the result if the output does not seem English
		if not utils.is_mostly_ascii(result.content["plot"]):
			logger.warning("Rejected translation: output does not appear to be English.")
			logger.info("Translated plot:\n%s", result.content["plot"])
			continue

		# Compute a similarity score between original and translated plot to
		# have a rough estimate of how much the meaning changed during translation.
		s1 = plot.split("\n")[0]
		s2 = result.content["plot"].split("\n")[0]

		res = SequenceMatcher(None, s1, s2).ratio()
		logger.info("Plot similarity score: %.2f", res)

		output_dir = Path("output") / date.today().strftime("%Y-%m-%d") / title
		output_dir.mkdir(parents=True, exist_ok=True)
		(output_dir / "original.json").write_text(article_data.model_dump_json(indent=2))
		(output_dir / "description.json").write_text(result.model_dump_json(indent=2))

		gcs_utils.upload(
			result.model_dump_json(),
			f"movies/{date.today().strftime('%Y-%m-%d')}/{title}/description.json"
		)

async def generate_translation(article_data: ArticleData, k: int, target_language: str = "en") -> ArticleData:
	"""Translate a Wikipedia movie article.
	Args:
		article_data (ArticleData): The article data to translate
		k (int): number of intermediary languages to translate to
		target_language (str): language code for the final output language
	Return:
		The translated article data as an ArticleData object
	"""
	translated_sections = {}
	chain = utils.generate_language_chain(k, source_language="en", target_language=target_language)
	language_names = " => ".join([LANGUAGES[code] for code in chain])
	logger.info("Languages to use %s", language_names)

	# Gather all sections to translate in a single flat dict for easier processing
	sections_to_translate = {
		"title": article_data.title,
		"infobox": utils.dict_to_newline_string(article_data.infobox),
	}
	sections_to_translate.update(article_data.content)

	for idx, section in enumerate(sections_to_translate):
		logger.info("Translating %s (%d of %d)", section, idx+1, len(sections_to_translate))

		text = sections_to_translate[section]
		if len(text) > 5000:
			logger.info("%s length=%d, truncating to 5000 characters", section, len(text))
			text = text[:5000]

		if section == "plot":
			# Each paragraph gets an independent language chain for more varied degradation
			translated_paragraphs = []
			for para in text.split("\n\n"):
				if not para.strip():
					translated_paragraphs.append(para)
					continue

				para_chain = utils.generate_language_chain(k, source_language="en", target_language=target_language)
				logger.debug("Paragraph chain: %s", " => ".join([LANGUAGES[code] for code in para_chain]))
				for previous, current in zip(para_chain, para_chain[1:]):
					result = await translator.translate(para, src=previous, dest=current)
					para = result.text
				translated_paragraphs.append(para)

			text = "\n\n".join(translated_paragraphs)
			text = utils.flatten_entities(text)
		else:
			for previous, current in zip(chain, chain[1:]):
				translated = await translator.translate(text, src=previous, dest=current)
				text = translated.text

		text = utils.cleanup_translation(text)
		translated_sections[section] = text
	
	# Build a new ArticleData object with the translated content;
	# parse infobox back to dict and keep non-content fields unchanged.
	translated = ArticleData(
		title=translated_sections["title"],
		content={key: translated_sections[key] for key in article_data.content},
		infobox=utils.newline_string_to_dict(translated_sections["infobox"]),
		metadata=article_data.metadata,
		img=article_data.img
	)

	return translated
