import os
import pytest
from unittest.mock import patch, Mock

from bs4 import BeautifulSoup
from pytest_schema import schema

# Mock Google Cloud client creations before importing the main library
with (
    patch("google.cloud.storage.Client"),
    patch("google.cloud.secretmanager.SecretManagerServiceClient")
):
    from src import translate


@pytest.fixture
def mock_soup():
    """Create a soup object from the local source html."""
    source_html = os.path.join(os.path.dirname(__file__), "mocks", "Alien.html")
    with open(source_html) as f:
          return BeautifulSoup(f.read(), "html.parser")


def test_get_title(mock_soup):
    """Test content parser for title."""
    assert translate.get_title(mock_soup) == "Alien"

def test_get_plot(mock_soup):
    """Test content parser for plot section."""
    expected = ("The commercial space tug Nostromo is returning to Earth with a seven-member crew in stasis: "
        "Captain Dallas, Executive Officer Kane, Warrant Officer Ripley, Navigator Lambert, "
        "Science Officer Ash, and engineers Parker and Brett. Detecting a transmission from a nearby moon, "
        "the ship's computer, Mother, awakens the crew. Per company policy requiring any potential distress "
        "signal be investigated, they land on the moon despite Parker's protests, sustaining damage "
        "from its atmosphere and rocky landscape. The engineers stay on board for repairs while Dallas, "
        "Kane, and Lambert investigate the terrain. They discover the signal originates from a derelict "
        "alien ship and enter it, losing contact with the Nostromo. Ripley deciphers part of the transmission, "
        "determining it as a warning, but cannot relay the information to those on the derelict ship."
        "\n\n"
        "Second paragraph."
        "\n\n"
        "Third paragraph.")

    assert translate.get_plot(mock_soup) == expected

def test_get_cast(mock_soup):
    """Test content parser for cast section."""
    expected = ("See also: List of Alien (film series) characters"
        "\n"
        "Tom Skerritt as Dallas, captain of the Nostromo. Skerritt had been approached early "
        "in the film's development, but declined as it did not yet have a director and had a very low budget. "
        "Later, when Scott was attached as director and the budget had been doubled, Skerritt accepted "
        "the role.[11][12]"
        "\n"
        "Sigourney Weaver as Ripley, the warrant officer aboard the Nostromo. Weaver, who had "
        "Broadway experience but was relatively unknown in film, impressed Scott, Giler, and Hill with her audition. "
        "She was the last actor to be cast for the film and performed most of her screen tests in-studio as the "
        "sets were being built.[12][13] The role of Ripley was Weaver's first leading role in a motion "
        "picture and earned her nominations for a Saturn Award for Best Actress and a BAFTA award for "
        "Most Promising Newcomer to Leading Film Role.[14]")
    
    assert translate.get_cast(mock_soup) == expected

def test_get_infobox(mock_soup):
    """Test content parser for infobox."""
    expected = {
        "Productioncompanies": "20th Century Fox\nBrandywine Productions[1][2]",
        "Distributed by": "20th Century Fox",
        "Release dates": "May 25, 1979 (1979-05-25) (United States)\nSeptember 6,\n1979 (1979-09-06) (United Kingdom)",
        "Running time": "116 minutes[3]",
        "Countries": "United Kingdom\nUnited States[1][2]",
        "Language": "English",
        "Budget": "$11 million[lower-alpha 1][5]",
        "Box office": "$184.7 million[5][6]"
    }
    assert translate.get_movie_infobox(mock_soup) == expected


@patch("src.translate.translator")
def test_generated_schema(mock_translate):
    """Validate high level schema of the translated description."""
    mock_translate.translate.return_value = Mock(text="")

    sections_to_translate = {
        "title": "A title",
        "plot": "Meaningful description.",
        "cast": "Tom Skellick as Jack\nNick Hardfloor as The Hammer",
        "infobox": "key1:value1\n\nkey2:value2"
    }
    translation = translate.generate_translation(sections_to_translate, 2)

    expected_schema = schema({
        "plot": str,
        "cast": str,
        "infobox": dict,
        "metadata": {
            "title": str
        }
    })
    assert expected_schema.is_valid(translation)


@pytest.mark.parametrize(
    "url_title,expected",
    [
        ("The_Departed", "The Departed"),
        ("Braveheart", "Braveheart"),
        ("American_History_X", "American History X"),
        ("Capernaum_(film)", "Capernaum"),
        ("City_of_God_(2002_film)", "City of God"),
        ("It%27s_a_Wonderful_Life", "It's a Wonderful Life"),
        ("Hachi:_A_Dog%27s_Tale", "Hachi: A Dog's Tale"),
        ("Kill_Bill:_Vol._1", "Kill Bill: Vol. 1"),
        ("Howl%27s_Moving_Castle_(film)", "Howl's Moving Castle")
    ])
def test_title_formatting(url_title, expected):
    """Test transformation from url encoded title to an article title."""
    assert translate.format_title(url_title) == expected