import pytest
from unittest.mock import patch, Mock

with patch("google.cloud.storage.Client"):
    import app as main


@pytest.fixture()
def app():
    app = main.app
    app.config.update({
        "TESTING": True,
    })

    yield app

@pytest.fixture()
def client(app):
    return app.test_client()


def test_person_generation_request(client):
    """Test content generation request for people."""
    with patch("src.get_person_info.batch_translate_and_upload") as mock_batch_translate_and_upload:
        response = client.get("/_generate", query_string={"type": "PERSON"}, headers={"X-Appengine-Cron": "1"})
        mock_batch_translate_and_upload.assert_called()
        assert response.status_code == 200

def test_movie_generation_request(client):
    """Test content generation request for people."""
    with patch("src.translate.batch_translate_and_upload") as mock_batch_translate_and_upload:
        response = client.get("/_generate", query_string={"type": "MOVIE"}, headers={"X-Appengine-Cron": "1"})
        mock_batch_translate_and_upload.assert_called()
        assert response.status_code == 200