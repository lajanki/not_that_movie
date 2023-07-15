import json
import logging
import re

from google.cloud import secretmanager


def strip_ref_tokens(text):
	"""Strip reference tokens, such as [1]."""
	return re.sub("(\[.*\])", "", text)

def dict_to_newline_string(dict_):
	"""Convert a dictionary to a key: value string for translatation
	purposes. Split each key newlines.
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

def parse_title(url_title):
	"""Parse a movie title from a url title,
	eg. Dunkirk_(2017_film) => Dunkirk
		The Wages of Fear => The Wages of Fear
	"""
	PATTERN = "([\w\-:% ]+)(_\(.*\))?"
	url_title = url_title.replace("_", " ")
	match = re.search(PATTERN, url_title)
	return match.group(1).strip()

def format_as_html(content):
	"""Convert the plot and cast sections of a stored
	movie file to html.
	"""
	plot = "".join([ f"<p>{p}</p>" for p in content["plot"].split("\n") if p ])
	cast_items = [ f"<li>{p}</li>" for p in content["cast"].split("\n") if p ]
	cast = "<ul>" + "".join(cast_items) + "</ul>"

	content.update({
		"plot": plot,
		"cast": cast
	})

	return content

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
