import argparse
from flask import (
	Flask,
	render_template,
	request,
	abort
)

from src import (
	translate,
	get_person_info,
	gcs_utils,
	utils
)


app = Flask(__name__)

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/movie_index")
def movie_index():
	return render_template("movie_index.html")

@app.route("/_generate")
def generate_descriptions():
	"""Generate a set of new descriptions, either movies or people, and write to Cloud Storage."""
	# Only respond to cron request originating from App Engine
	if "X-Appengine-Cron" in request.headers:
		batch_size = int(request.args["batch_size"])
		k = int(request.args.get("k", 2))

		if request.args.get("type") == "people":
			get_person_info.batch_translate_and_upload(batch_size, k)
		else:
			translate.batch_translate_and_upload(batch_size, k)

		return "OK", 200

	abort(500, "Bad request")
	
@app.route("/_get")
def fetch_movie_description():
	"""Fetch a movie description from the bucket; either the one given
	as argument or a randomly chosen one if no argument provided.
	"""
	path = request.args.get("path")
	if path:
		data = gcs_utils.download_description(path)
	else:
		data = gcs_utils.download_random_content("movies")

	data = utils.format_as_html(data)
	return data, 200
	
@app.route("/_get_movie_list")
def fetch_movie_index():
	"""Fetch list of current movies from Cloud Storage."""
	data = gcs_utils.fetch_all_movies()
	return data, 200

@app.route("/_get_person")
def fetch_person_description():
	"""Fetch a random preson from the bucket."""
	data = gcs_utils.download_random_content("people")

	# convert description to html
	data["description"] = "".join([ f"<p>{p}</p>" for p in data["description"].split("\n\n") if p ])
	return data, 200


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	args = parser.parse_args()

	app.run()
