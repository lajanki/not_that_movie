import json
import logging
import random
import re

from collections import Counter
from googletrans import LANGUAGES

from jobs import BASE


logger = logging.getLogger(__name__)


def generate_language_chain(k, source_language, target_language):
	"""Generate a language chain for translation.
	 
	Randomizes a list of k+2 language codes with the specified
	initial and last languages.

	Args:
		k (int): the number of intermediary languages to use
		source_language (str): the source language code, e.g. "en"
		target_language (str): the target language code, e.g. "fr"
	Return:
		A list of language codes to use for translation in order.
	"""
	# Ensure none of the intermediary languages are the same as source or target language
	available_languages = set(LANGUAGES.keys()) - {source_language, target_language}
	languages = random.choices(list(available_languages), k=k)
	languages = [source_language] + languages + [target_language]
	return languages

def dict_to_newline_string(dict_):
	"""Convert a dictionary to a newline delimited key:value string.
	Only flat dictionaries are supported.
	 
	For instance
		dict_to_newline_string({
			key1: value1,
			key2: value2
		})
		
		```
		key1:value1
		
		key2:value2
		```
	"""
	return "\n\n".join([f"{key}:{value}" for key,value in dict_.items()])

def newline_string_to_dict(text):
	"""Parse a newline delimited key: value string as dict.

	Inverse of dict_to_newline_string; used to map translated
	infobox content back to a dict.
	"""
	data = {}
	items = text.split("\n\n")
	
	for line in items:
		# The key, value separator may have been removed in the translation
		if ":" not in line:
			logger.warning("Can't parse '%s' as key: value, ignoring...", line)
			continue
			
		tokens = line.split(":")
		data[tokens[0]] = tokens[1].strip()

	return data

def format_as_html(content):
	"""Convert various sections parsed from an article as html.
	
	Args:
		content (dict): a dict of sections to format, e.g. plot, cast, description
	Return:
		A dict with the same keys as the input but with the content formatted as html.
	"""
	# plot and cast for a movie article
	plot = "".join([ f"<p>{p}</p>" for p in content.get("plot", "").split("\n\n") if p ])
	cast_items = [ f"<li>{p}</li>" for p in content.get("cast", "").split("\n") if p ]
	cast = "<ul>" + "".join(cast_items) + "</ul>"

	# description for a person article
	description = "".join([ f"<p>{p}</p>" for p in content.get("description", "").split("\n\n") if p ])

	content.update({
		"plot": plot,
		"cast": cast,
		"description": description
	})

	return content

def cleanup_source_text(text, replace_newlines=True):
	"""Cleanup various whitespace and meta tokens from parsed html
	document source text.
	text.

	The source text may contain various whitespace characters and
	ref tokens like [1], [2] etc.

	Args:
		text (str): the text to clean up
		replace_newlines (bool): whether to replace newlines with whitespace
	Return:
		The cleaned up text
	"""
	replace_map = str.maketrans({
		"\u200b": "", # zero-width space
		"\xa0": "" # non-breaking space
	})
	text = text.translate(replace_map) 

	if replace_newlines:
		text = text.replace("\n", "")

	# remove consecutive whitespace characters
	text = re.sub("[ \\t]{2,}", " ", text)

	# strip ref tokens
	text = re.sub("(\[.*?\])", "", text)
	
	return text.strip()

def cleanup_translation(s):
	"""Cleanup common erroneous characters introduced by translation:
	 * extra whitespace in dollar amounts $ 300 => $300
	 * missing whitespace between sentence boundaries
	"""
	s = s.replace("$ ", "$")
	# Add whitespace if next character is uppercase
	s = re.sub(r"([a-z])(\.)([A-Z])", r"\g<1>. \g<3>", s)
	return s

def select_weighted_list_of_movie_names(batch_size):
	"""Generate a random list of movie names based on source data files.
	
	Weights from data/weight_config.json are used to determine the
	likelihood of a movie name being selected from each source file.

	The weights are relative to each other with higher value corresponding to the likelihood of that
	file being used more often.

	Args:
		batch_size (int): the number of movie names to select
	Return:
		A list of selected movie names
	"""
	with open(BASE / "data" / "weight_config.json") as f:
		weight_config = json.load(f)

	# Generate a weighted list of source files to read and convert the list of (potentially) repeated file
	# names to a Counter
	sampled_source_files = random.choices(
		list(weight_config.keys()),
		weights=weight_config.values(),
		k=batch_size
	)
	c = Counter(sampled_source_files)

	source_titles = []
	# Select movie names from each chosen file according to the count
	for file in c:
		with open(BASE / "data" / file) as f:
			titles = [ row.strip() for row in f.readlines() if row.strip() and not row.startswith("#") ]
			source_titles.extend(random.sample(titles, c[file]))

	return source_titles
