import json
import logging
import random
import re
import requests
from datetime import date
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup
from googletrans import Translator, LANGUAGES
import httpx

from app import (
	create_image,
	ENV,
	gcs_utils,
	utils,
)


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
	titles = utils.select_weighted_list_of_movie_names(batch_size)
	for url_title in titles:
		logging.info("##%s", url_title)
		logging.info("%s/%s", BASE_URL, url_title)

		soup = make_soup(url_title)
		if not soup.select("#Plot"):
			logging.error(f"https://en.wikipedia.org/wiki/{url_title} doesn't apper to be a valid movie article.")
			continue

		title = format_title(url_title)
			
		# Generate and upload a poster image
		prompt = f"{title} Movie Poster"
		img_blob = gcs_utils.upload(
			create_image.create_image_by_env[ENV](prompt),
			f"movies/{date.today().strftime('%Y-%m-%d')}/{title}/image.png",
			content_type="image/png"
		)

		# Generate a translation
		sections_to_translate = {
			"title": title,
			"plot": get_plot(soup),
			"cast": get_cast(soup),
			"infobox": utils.dict_to_newline_string(get_movie_infobox(soup))
		}
		result = generate_translation(sections_to_translate, k)

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
		text = sections_to_translate[section]
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

	# Move translated title to a dedicated metadata section
	translated_sections["metadata"] = {
		"title": translated_sections.pop("title").title()
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
	"""Fetch html content based on movie title from the Wikipedia API
	https://en.wikipedia.org/api/rest_v1/#/Page%20content/get_page_html__title_
	Return:
		The parsed content of the page as BeautifulSoup object
	"""
	headers = {
		"User-Agent": "NotThatMovieBot/1.0 (https://not-that-movie.net rrt-info-1.20205@protonmail.com)"
	}
	r = requests.get(f"{BASE_URL}/{title}", headers=headers)
	r.raise_for_status()
	soup = BeautifulSoup(r.text, "html.parser")

	# Attach the original search term title to the soup
	soup.url_title = title
	
	return soup

def get_title(soup):
	"""Parse movie title from the right hand infobox table header."""
	return soup.find("th", class_="infobox-above").text.strip()

def get_plot(soup):
    """Get content from the Plot section.
	Return
		string delimited by double newline
	"""
    paragraphs = [
        utils.cleanup_source_text(tag.text)
        for tag in soup.select("section > h2#Plot")[0].next_siblings
    ]

    return "\n\n".join([p for p in paragraphs if p])

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
			paragraphs.append(tag.text)
		elif tag.name == "ul":
			paragraphs.extend([item.text for item in tag.select("li")])

	# Drop the first paragprah if it mathces a link to a further article
	section_prefixes = [
		"main article",
		"see also",
		"further information"
	]
	if paragraphs and any([pre in paragraphs[0].lower() for pre in section_prefixes]):
		paragraphs = paragraphs[1:]

	return "\n".join([ utils.cleanup_source_text(p) for p in paragraphs if p ])

def _get_infobox(soup, headers_to_extract):
	"""Get selected metadata from the right hand side info table.
	Args:
		soup (bs4.BeautifulSoup): the soup object to parse
		headers_to_extract (list): list of keys to extract
	Return:
		a dict of parsed content
	"""
	# Loop through all <tr> tags looking for selected header terms
	# and try to parse its content
	metadata = {}
	for tag in soup.select("table.infobox > tbody > tr"):
		if any([header in utils.cleanup_source_text(tag.text) for header in headers_to_extract]):
			try:
				header = utils.cleanup_source_text(tag.find("th").text)
				value = utils.cleanup_source_text(tag.find("td").text, replace_newlines=False)
				metadata[header] = value
			except AttributeError as e:
				continue
	
	return metadata

def get_movie_infobox(soup):
	"""Get selected metadata from the right side info table.
	Return:
		a dict of parsed content
	"""
	headers_to_extract = [
		"Based on",
		"Box office",
		"Budget",
		"Countries",
		"Directed by",
		"Distributed by",
		"Language",
		"Production companies",
		"Production company",
		"Productioncompanies",
		"Release date",
		"Release dates",
		"Running time",
	]

	return _get_infobox(soup, headers_to_extract)

def format_title(url_title):
	"""Format a displayable article title from a Wikipedia url title:
	 * url decode
	 * replace underscores
	 * remove (film) suffix
	"""
	title = unquote(url_title)
	title = re.sub("\(.*film\)", "", title)
	return title.replace("_", " ").strip()
