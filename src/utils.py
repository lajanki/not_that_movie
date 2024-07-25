import json
import logging
import random
import re

from collections import Counter
from google.cloud import secretmanager



def dict_to_newline_string(dict_):
	"""Convert a dictionary to a key: value string for translatation
	purposes. Split each key by newlines.
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
	Inverse of above.
	"""
	data = {}
	items = text.split("\n\n")
	
	for line in items:
		# The key, value separator may have been removed in the translation
		if ":" not in line:
			logging.warning("Can't parse '%s' as key: value, ignoring...", line)
			continue
			
		tokens = line.split(":")
		data[tokens[0]] = tokens[1].strip()

	return data

def format_as_html(content):
	"""Convert various sections parsed from an article as html."""
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
	"""Cleanup various whitespace and meta tokens from the parsed source
	text left from inline html elements such as <a>
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

def get_openai_secret():
	"""Fetch OpenAI API key from Secret Manager."""
	client = secretmanager.SecretManagerServiceClient()
	response = client.access_secret_version(name="projects/webhost-common/secrets/openai_api_key/versions/1")
	return response.payload.data.decode()

def select_weighted_list_of_movie_names(batch_size):
	"""Generate a random list of batch_size movie names selected from all the source list files in data/
	according to the weights in data/weight_config.json.
	The weights are relative to each other with higher value corresponding to the likelihood of that
	file being used more often.
	Return
		A list of selected movie names
	"""
	with open("data/weight_config.json") as f:
		weight_config = json.load(f)

	# Generate a weighted list of source files to read and convert the list of (potentially) repeated file
	# names to a Counter
	sampled_source_files = random.choices(list(weight_config.keys()), weights=weight_config.values(), k=batch_size)
	c = Counter(sampled_source_files)

	source_titles = []
	# Select movie names from each chosen file according to the count
	for file in c:
		with open(f"data/{file}") as f:
			titles = [ row.strip() for row in f.readlines() if row.strip() and not row.startswith("#") ]
			source_titles.extend(random.sample(titles, c[file]))

	return source_titles