import json
import logging
import random
from datetime import date

from src import (
	utils,
	gcs_utils,
	create_image,
	translate,
	ENV,
)


def batch_translate_and_upload(batch_size, k=2):
	"""Translate a random sample of titles for person articles and store results to
	Cloud Storage bucket.
	Args:
		batch_size (int): number of translations to generate
		k (int): number of intermediary languages to use
	"""
	titles = random.sample(get_full_people_list(), batch_size)
	for url_title in titles:
		logging.info("##%s", url_title)
		logging.info("%s/%s", translate.BASE_URL, url_title)

		soup = translate.make_soup(url_title)
		title = translate.get_title(soup)
			
		# Generate and upload a poster image
		prompt = get_person_portrait_prompt()
		img_blob = gcs_utils.upload(
			create_image.create_image_by_env[ENV](prompt),
			f"people/{date.today().strftime('%Y-%m-%d')}/{title}/image.png",
			content_type="image/png"
		)

		# Generate a translation
		sections_to_translate = {
			"title": translate.get_title(soup),
			"description": get_description(soup),
			"infobox": utils.dict_to_newline_string(get_person_infobox(soup))
		}
		result = translate.generate_translation(sections_to_translate, k)
		result["img"] = img_blob.public_url
		result["metadata"].update({
			"original_title": translate.get_title(soup),
			"url_title": url_title
		})

		gcs_utils.upload(
			json.dumps(result),
			f"people/{date.today().strftime('%Y-%m-%d')}/{title}/description.json"
		)

def get_description(soup):
	"""Get a short description for this person; the first paragraph in the article.
	Return
		string delimited by double newline
	"""
	paragraphs = [ tag.text for tag in  soup.select("body > section:first-child > p")]

	# The raw parsed text content likely includes various whitespace character
	# form inline elements such as <a>.
	# Cleanup each paragraph and merge to a single string
	char_map = str.maketrans({
		"\n": " ",
		"\t": ""
	})
	content = "\n\n".join([ p.translate(char_map) for p in paragraphs if p ])
	return content

def get_person_infobox(soup):
	"""Get selected metadata from the right side info table.
	Return:
		a dict of parsed content
	"""
	headers_to_extract = [
		"Born",
		"Died",
		"Alma mater",
		"Education",
		"Nationality",
		"Citizenship",
		"Occupations",
		"Occupation",
		"Years active",
		"Political party",
		"Spouse",
		"Spouses",
		"Partner",
		"Partners",
		"Children",
		"Works",
		"Known for",
		"Relatives",
		"Awards"
	]

	return translate._get_infobox(soup, headers_to_extract)

def get_full_people_list():
	"""Get a full list of people from source data files."""
	with open("./data/actors.txt") as f, open("./data/directors.txt") as g:
		people = [ row.strip() for row in f.readlines() + g.readlines()
			 if row.strip() and not row.startswith("#") ]
	
	return people

def get_person_portrait_prompt():
	"""Select a random prompt for a person portrait image."""
	with open("data/portrait_prompts.txt") as f:
		prompts = [ row.strip() for row in f.readlines() if row.strip() and not row.startswith("#") ]
	return random.choice(prompts)