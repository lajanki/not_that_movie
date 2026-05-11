from flask import (
	Flask,
	render_template,
	request,
)

from jobs import gcs_utils, utils
from jobs.constants import ContentType


app = Flask(__name__)


@app.route("/")
def index():
	return render_template("index.html")

@app.route("/movie_index")
def movie_index():
	return render_template("movie_index.html")
	
@app.route("/_get")
def fetch_movie_description():
	"""Fetch a movie description from the bucket; either the one given
	as argument or a randomly chosen one if no argument provided.
	"""
	path = request.args.get("path")
	if path:
		data = gcs_utils.download_description(path)
	else:
		data = gcs_utils.download_random_content(ContentType.MOVIE.name)

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
	data = gcs_utils.download_random_content(ContentType.PERSON.name)
	data = utils.format_as_html(data)
	return data, 200
