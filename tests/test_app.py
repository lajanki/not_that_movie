import pytest
from unittest.mock import patch, Mock

with patch("google.cloud.storage.Client"):
    from app.views import app as flask_app


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
    with patch("app.views.render_template") as mock_render:
        mock_render.return_value = "patched-render"
        response = client.get("/")
        mock_render.assert_called_once_with("index.html")
        assert response.status_code == 200
        assert b"patched-render" in response.data

def test_person_generation_request(client):
    """Test content generation request for people."""
    with patch("app.get_person_info.batch_translate_and_upload") as mock_batch_translate_and_upload:
        response = client.get("/_generate", query_string={"type": "PERSON"}, headers={"X-Appengine-Cron": "1"})
        mock_batch_translate_and_upload.assert_called()
        assert response.status_code == 200

def test_movie_generation_request(client):
    """Test content generation request for people."""
    with patch("app.translate.batch_translate_and_upload") as mock_batch_translate_and_upload:
        response = client.get("/_generate", query_string={"type": "MOVIE"}, headers={"X-Appengine-Cron": "1"})
        mock_batch_translate_and_upload.assert_called()
        assert response.status_code == 200