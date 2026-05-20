import pytest
from unittest.mock import patch, Mock

with patch("google.cloud.storage.Client"):
    from webserver.views import app as flask_app


@pytest.fixture()
def app():
    flask_app.config.update({
        "TESTING": True,
    })

    yield flask_app

@pytest.fixture()
def client(app):
    return app.test_client()


def test_index_request(client):
    """Request to the root should render the index page."""
    with patch("webserver.views.render_template") as mock_render:
        mock_render.return_value = "patched-render"
        response = client.get("/")
        mock_render.assert_called_once_with("index.html")
        assert response.status_code == 200
        assert b"patched-render" in response.data

def test_fetch_movie_description_with_path(client):
    """Should call download_description when path is provided."""
    with patch("webserver.views.gcs_utils.download_description") as mock_download, \
         patch("webserver.views.utils.format_as_html") as mock_format:
        mock_download.return_value = {
            "metadata": {"title": "Test Title"},
            "plot": "Test plot",
            "cast": "Test cast",
            "description": "Test description",
            "infobox": {},
            "img": "test.jpg"
        }
        mock_format.return_value = "formatted-data"
        response = client.get("/_get?path=some/path.txt")
        mock_download.assert_called_once_with("some/path.txt")
        mock_format.assert_called_once_with({
            "title": "Test Title",
            "content": {
                "plot": "Test plot",
                "cast": "Test cast",
                "description": "Test description"
            },
            "infobox": {},
            "metadata": {"title": "Test Title"},
            "img": {"prompt": "", "url": "test.jpg"}
        })
        assert response.status_code == 200
        assert b"formatted-data" in response.data

def test_fetch_movie_description_random(client):
    """Should call download_random_content when no path is provided."""
    with patch("webserver.views.gcs_utils.download_random_content") as mock_random, \
         patch("webserver.views.utils.format_as_html") as mock_format:
        mock_random.return_value = {
            "metadata": {"title": "Random Title"},
            "plot": "Random plot",
            "cast": "Random cast",
            "description": "Random description",
            "infobox": {},
            "img": "random.jpg"
        }
        mock_format.return_value = "formatted-random"
        response = client.get("/_get")
        mock_random.assert_called_once()
        mock_format.assert_called_once_with({
            "title": "Random Title",
            "content": {
                "plot": "Random plot",
                "cast": "Random cast",
                "description": "Random description"
            },
            "infobox": {},
            "metadata": {"title": "Random Title"},
            "img": {"prompt": "", "url": "random.jpg"}
        })
        assert response.status_code == 200
        assert b"formatted-random" in response.data
