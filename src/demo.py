# Runnable script for generating sample translations for demonstration purposes.
#
# Run from the root folder with
# 	python -m src.demo <title>

import argparse
import json

from src import (
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


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Chain translate Wikpedia movie plots")
	parser.add_argument("title", help="Wikipedia article url title")
	parser.add_argument("--person", help="Extract person information instead of movie", action="store_true")
	parser.add_argument("--k", help="Number of intermediary languages", type=int, default=2)
	parser.add_argument("--target_language", help="Target language for final translation", default="en")
	args = parser.parse_args()

	if args.person:
		print_person(args.title, args.k)
	else:
		print_movie(args.title, args.k)

