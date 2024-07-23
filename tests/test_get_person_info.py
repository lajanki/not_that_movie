
import os
import pytest
from unittest.mock import patch, Mock

from bs4 import BeautifulSoup
from pytest_schema import schema

with patch("google.cloud.storage.Client"):
    from src import get_person_info


@pytest.fixture
def mock_soup():
    """Create a soup object from the local source html."""
    source_html = os.path.join(os.path.dirname(__file__), "mocks", "Mike Myers.html")
    with open(source_html) as f:
          return BeautifulSoup(f.read(), "html.parser")


def test_get_description(mock_soup):
    """Test content parser for person description."""
    expected = (
        'Michael John Myers OC (born May 25, 1963) is a Canadian-American actor, '
        'comedian, and filmmaker. His accolades include seven MTV Movie & TV Awards, a Primetime Emmy Award, and a Screen Actors Guild Award. '
        'In 2002, he was awarded a star on the Hollywood Walk of Fame. In 2017, he was named an Officer of the Order of Canada for '
        '"his extensive and acclaimed body of comedic work as an actor, writer, and producer."\n\n'
        'Following a series of appearances on '
        'several Canadian television programs, Mike Myers attained recognition during his six seasons as a cast member on the NBC '
        'sketch comedy series Saturday Night Live from 1989 to 1995, which won him the Primetime Emmy Award for '
        'Outstanding Writing for a Variety Series. He subsequently earned praise and numerous accolades for '
        'playing the title roles in the Wayne\'s World (1992–1993), Austin Powers (1997–2002), and Shrek (2001–present) franchises, '
        'the latter of which is the second highest-grossing animated film franchise. Myers also played the titular star '
        'in the 2003 live-action adaptation of the Dr. Seuss book The Cat in the Hat.\n\n'
        'Myers acted sporadically in the 2010s, '
        'having supporting roles in Terminal and Bohemian Rhapsody (both 2018). He made his directorial '
        'debut with the documentary Supermensch: The Legend of Shep Gordon (2013), which premiered at the Toronto International Film Festival. '
        'He created and starred in the 2022 Netflix original series, The Pentaverate, and appeared in David O. '
        'Russell\'s Amsterdam.'
    )

    assert get_person_info.get_description(mock_soup) == expected

def test_get_person_infobox(mock_soup):
    """Test content parser for person infobox."""
    expected = {
        "Born": "Michael John Myers\n (1963-05-25) May 25, 1963\n (age61)\nToronto, Ontario, Canada",
        "Citizenship": "Canada\nUnited Kingdom\nUnited States",
        "Occupations": "Actor\ncomedian\nfilmmaker\nsinger\nmusician\nproducer",
        "Spouses": "Robin\n Ruzan\n \n\n(m.1993; div.2006)\n\n\n\n\n\n\n\nKelly Tisdale \n(m.2010)",
        "Children": "3",
        "Relatives": "Paul Myers (brother)"
    }
    
    assert get_person_info.get_person_infobox(mock_soup) == expected
