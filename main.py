import argparse
from flask import (
	Flask,
	render_template,
	request,
	abort
)

from src import (
	translate,
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
    """Generate a set of new movie descriptions and write to Cloud Storage."""
    # Only respond to cron request originating from App Engine
    if "X-Appengine-Cron" in request.headers:
        batch_size = int(request.args["batch_size"])
        k = int(request.args.get("k", 2))

        translate.batch_translate_and_upload(batch_size, k)
        return "OK", 200

    abort(500, "Bad request")
    
@app.route("/_get")
def fetch_description():
    """Fetch a movie description from the bucket; either the one given
    as argument or a randomly chosen one.
    """
    path = request.args.get("path")
    if path:
        data = gcs_utils.download_description(path)
    else:
        data = gcs_utils.download_random()

    data = utils.format_as_html(data)
    return data, 200
    
@app.route("/_get_movie_list")
def fetch_movie_index():
    """Fetch list of current movies from Cloud Storage."""
    data = gcs_utils.fetch_all()
    return data, 200
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    app.run(debug=args.debug)
