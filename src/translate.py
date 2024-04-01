import argparse
import json
import logging
import random
import requests
from urllib.parse import quote
from datetime import date

from bs4 import BeautifulSoup
import httpx
from googletrans import Translator, LANGUAGES

from src import (
	utils,
	gcs_utils,
	create_image,
	ENV
)


logging.basicConfig(level=logging.INFO)

timeout = httpx.Timeout(10)
translator = Translator(timeout=timeout)

BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/html"

def batch_translate_and_upload(batch_size, k=2):
	"""Translate a random sample of titles and store results to
	Cloud Storage bucket.
	Args:
		batch_size (int): number of translations to generate
		k (int): number of intermediary languages to use
	"""
	with open("./data/movie_list.txt") as f:
		titles = [ row.strip() for row in f.readlines() ]
		
	titles = random.sample(titles, batch_size)
	for url_title in titles:
		logging.info("##%s", url_title)
		logging.info("%s/%s", BASE_URL, url_title)

		soup = make_soup(url_title)
		if not soup.select("#Plot"):
			logging.error(f"https://en.wikipedia.org/wiki/{quote(title)} doesn't apper to be a valid movie article.")
			continue

		title = get_title(soup)
			
		# Generate and upload a poster image
		prompt = f"{title} Movie Poster"
		img_blob = gcs_utils.upload(
			create_image.create_image_by_env[ENV](prompt),
			f"movies/{date.today().strftime('%Y-%m-%d')}/{title}/image.png",
			content_type="image/png"
		)

		# Generate a translation
		sections_to_translate = {
			"title": get_title(soup),
			"plot": get_plot(soup),
			"cast": get_cast(soup),
			"infobox": utils.dict_to_newline_string(get_infobox(soup))
		}
		result = generate_translation(sections_to_translate, k)

		# Add a (public) link to the related image
		result["img"] = img_blob.public_url

		gcs_utils.upload(
			json.dumps(result),
			f"movies/{date.today().strftime('%Y-%m-%d')}/{title}/description.json"
		)

def generate_translation(sections_to_translate, k, target_language="en"):
	"""Translate a single Wikipedia movie article.
	Args:
		sections_to_translate (dict): A mapping of sections fron the original article to translate
		k (int): number of intermediary languages to translate to
		target_language (str): language code for the final output language
	Return:
		A dict of the trasnalted section, similar to the input
	"""	
	translated_sections = {}
	chain = generate_language_chain(k, source_language="en", target_language=target_language)
	language_names = " => ".join([LANGUAGES[code] for code in chain])
	logging.info("Languages to use %s", language_names)
	for idx, section in enumerate(sections_to_translate):
		logging.info("Translating %s (%d of %d)", section, idx+1, len(sections_to_translate))
		# Remove citation tokens (ie. [1], [2] etc.)
		text = utils.strip_ref_tokens(sections_to_translate[section])
		if len(text) > 5000:
			logging.info("%s length=%d, truncating to 5000 characters", section, len(text))
			text = text[:5000]
		
		for previous, current in zip(chain, chain[1:]):
			translated = translator.translate(text, src=previous, dest=current)
			text = translated.text
		
		text = utils.cleanup_translation(text)
		translated_sections[section] = text

	# Convert infobox back to a dict
	translated_sections["infobox"] = utils.newline_string_to_dict(translated_sections["infobox"])

	# Move translated title to a dedicated metadata section and add the original title
	translated_sections["metadata"] = {
		"title": translated_sections.pop("title").title(),
		"original_title": sections_to_translate["title"]
	}
	
	return translated_sections

def generate_language_chain(k, source_language, target_language):
	"""Generate a random list of k+2 language codes with the specified
	initial and last languages.
	"""
	languages = random.choices(list(LANGUAGES.keys()), k=k)
	languages = [source_language] + languages + [target_language]
	return languages

def make_soup(title):
	"""Fetch html content based on movie title from Wikipedia API
	https://en.wikipedia.org/api/rest_v1/#/Page%20content/get_page_html__title_
	Return:
		The parsed content of the page as BeautifulSoup object
	"""
	r = requests.get(f"{BASE_URL}/{title}")
	r.raise_for_status()
	soup = BeautifulSoup(r.text, "html.parser")
	
	return soup

def get_title(soup):
	"""Parse movie title from the right hand infobox table header."""
	return soup.find("th", class_="infobox-above").text.strip()

def get_plot(soup):
	"""Get content from the Plot section.
	Return
		string delimited by double newline
	"""
	paragraphs = [ tag.text.strip() for tag in soup.select("section > h2#Plot")[0].next_siblings ]

	# The raw parsed text content likely includes various whitespace character
	# form inline elements such as <a>.
	# Cleanup each paragraph and merge to a single string
	char_map = str.maketrans({
		"\n": " ",
		"\t": ""
	})
	content = "\n\n".join([ p.translate(char_map) for p in paragraphs if p ])
	return content

def get_cast(soup):
	"""Get content from Cast section.
	The element hierarchy varies by page; get content from all
	<div>, <p> and <li> elements inside a <ul>
	Return:
		newline delimitted string
	"""
	paragraphs = []
	for tag in soup.select("#Cast, #Voice_cast, #Casting")[0].next_siblings:
		if tag.name in ("div", "p"):
			paragraphs.append(tag.text.strip())
		elif tag.name == "ul":
			paragraphs.extend([item.text for item in tag.select("li")])

	char_map = str.maketrans({
		"\n": " ",
		"\t": ""
	})

	content = "\n".join([ p.translate(char_map) for p in paragraphs if p ])
	return content

def get_infobox(soup):
	"""Get selected metadata from the right side info table.
	Return:
		a dict of parsed content
	"""
	KEY_HEADERS = [
		"Directed by",
		"Production companies",
		"Production company",
		"Productioncompanies",
		"Based on",
		"Distributed by",
		"Release dates",
		"Release date",
		"Running time",
		"Budget",
		"Box office",
		"Countries",
		"Language"
	]

	# Loop through all <tr> tags looking for selected header terms
	# and try to parse its content
	metadata = {}
	for tag in soup.select("table.infobox > tbody > tr"):
		if any([header in tag.text for header in KEY_HEADERS]):
			try:
				header = tag.find("th").text.strip("\n\t")
				value = tag.find("td").text.strip("\n")
				metadata[header] = value
			except AttributeError as e:
				continue
	
	return metadata

def print_sample_description(title, k):
	"""Generate and print a sample translation description from and input title."""
	soup = make_soup(title)
	res = generate_translation(soup, k)
	print(json.dumps(res, indent=2))


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Chain translate Wikpedia movie plots")
	parser.add_argument("title", help="Wikipedia article title")
	parser.add_argument("--k", help="Number of intermediary languages", type=int, default=2)
	parser.add_argument("--target_language", help="Target language for final translation", default="en")
	args = parser.parse_args()
	
	print_sample_description(args.title, args.k)

