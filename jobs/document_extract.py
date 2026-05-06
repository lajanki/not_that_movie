import logging
import re
import requests
from urllib.parse import unquote

from bs4 import BeautifulSoup

from . import utils


logger = logging.getLogger(__name__)


BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/html"



def make_soup(title):
	"""Fetch html content based on movie title from the Wikipedia API
	https://en.wikipedia.org/api/rest_v1/#/Page%20content/get_page_html__title_
	Return:
		The parsed content of the page as BeautifulSoup object
	"""

	# The API requires a User-Agent header
	# https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
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

def format_title(url_title):
	"""Format a displayable article title from a Wikipedia url title:
	 * url decode
	 * replace underscores
	 * remove (film) suffix
	"""
	title = unquote(url_title)
	title = re.sub(r"\(.*film\)", "", title)
	return title.replace("_", " ").strip()

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


# =================================
# Movie content parsing =
# =======================

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


# ==================================
# = Person content parsing =
# ==========================

def get_description(soup):
	"""Get a short description for this person; the first paragraph in the article.
	Return
		string with paragraphs delimited by double newline
	"""
	paragraphs = [
		utils.cleanup_source_text(tag.text)
		for tag in soup.select("body > section:first-child > p")
	]

	return "\n\n".join([p for p in paragraphs if p])

def get_person_infobox(soup):
	"""Get selected metadata from the right side info table.
	Return:
		a dict of parsed content
	"""
	headers_to_extract = [
		"Alma mater",
		"Awards",
		"Born",
		"Children",
		"Citizenship",
		"Died",
		"Education",
		"Known for",
		"Nationality",
		"Occupation",
		"Occupations",
		"Partner",
		"Partners",
		"Political party",
		"Relatives",
		"Spouse",
		"Spouses",
		"Works",
		"Years active",
		"Yearsactive",
	]

	return _get_infobox(soup, headers_to_extract)