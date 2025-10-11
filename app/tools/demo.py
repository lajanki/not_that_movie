# Helper functions for printing sample translations.
# run through cli.py.

import json

from app import (
	utils,
	translate,
	get_person_info
)


def print_movie(title, k):
	soup = translate.make_soup(title)
	sections_to_translate = {
		"title": translate.format_title(title),
		"plot": translate.get_plot(soup),
		"cast": translate.get_cast(soup),
		"infobox": utils.dict_to_newline_string(translate.get_movie_infobox(soup))
	}
	res = translate.generate_translation(sections_to_translate, k)
	print(json.dumps(res, indent=2))

def print_person(title, k):
	soup = translate.make_soup(title)
	sections_to_translate = {
		"title": translate.format_title(title),
		"description": get_person_info.get_description(soup),
		"infobox": utils.dict_to_newline_string(get_person_info.get_person_infobox(soup))
	}
	res = translate.generate_translation(sections_to_translate, k)
	print(json.dumps(res, indent=2))
