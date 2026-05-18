import argparse
import asyncio
import logging

from jobs import (
	generate_movie,
	generate_person
)



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Run a content generation job.")
	parser.add_argument("--type", type=str, required=True, choices=["movie", "person"],
						help="The type of content to generate; either 'movie' or 'person'.")
	parser.add_argument("--batch_size", type=int, default=1,
						help="Number of descriptions to generate in this batch.")
	parser.add_argument("--k", type=int, default=2,
						help="Number of intermediary languages to translate to.")
	parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
	args = parser.parse_args()

	if args.debug:
		logger = logging.getLogger("jobs")
		logger.setLevel(logging.DEBUG)

		# Ensure all handlers also use the same level
		for handler in logger.handlers:
			handler.setLevel(logging.DEBUG)


	if args.type == "movie":
		asyncio.run(generate_movie.batch_translate_and_upload(args.batch_size, args.k))
	if args.type == "person":
		asyncio.run(generate_person.batch_translate_and_upload(args.batch_size, args.k))
