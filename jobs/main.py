import argparse
import asyncio

from . import (
	generate_movie,
	generate_person,
)



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Run a content generation job.")
	parser.add_argument("--type", type=str, required=True, choices=["movie", "person"],
						help="The type of content to generate; either 'movie' or 'person'.")
	parser.add_argument("--batch_size", type=int, default=1,
						help="Number of descriptions to generate in this batch.")
	parser.add_argument("--k", type=int, default=2,
						help="Number of translations to generate for each description.")
	args = parser.parse_args()

	if args.type == "movie":
		asyncio.run(generate_movie.batch_translate_and_upload(args.batch_size, args.k))
	if args.type == "person":
		asyncio.run(generate_person.batch_translate_and_upload(args.batch_size, args.k))
