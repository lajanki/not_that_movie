import pytest

from jobs import (
	utils
)



def test_format_as_html():
    """Test html formatting of parsed content."""
    article_data = {
        "title": "A title",
        "content": {
            "plot": "one\n\ntwo\n\nthree\n\nfour.",
            "cast": "James as lion\nJohn as submarine"
        },
        "infobox": {
            "key1": "value1",
            "key2": "value2"
        },
        "metadata": {
            "key": "value"
        },
        "img": {
            "url": "https://example.com/image.png"
        }
    }

    expected = {
        "title": "A title",
        "content": {
            "plot": "<p>one</p><p>two</p><p>three</p><p>four.</p>",
            "cast": "<ul><li>James as lion</li><li>John as submarine</li></ul>",
            "description": ""
        },
        "infobox": {
            "key1": "value1",
            "key2": "value2"
        },
        "metadata": {
            "key": "value"
        },
        "img": {
            "url": "https://example.com/image.png"
        }
    }

    assert utils.format_as_html(article_data) == expected

@pytest.mark.parametrize(
    "test_string,expected",
    [
        ("Budget: $ 45 million", "Budget: $45 million"),
        ("one two.Skidoo", "one two. Skidoo"),
        ("one two.three", "one two.three")
    ])
def test_cleanup_translation(test_string, expected):
    """Test cleanup of common erroneous characters introduced by translation."""
    assert utils.cleanup_translation(test_string) == expected

    # Longer sample
    s = """Hadilano LiF Lable Kauzuku, the Korean man helped Japan,
    to find one gold to be happy.The Sook's great role is to help them read the
    Ur's Humans.Two who end up to love, under the imagination of preparing helpang.His
    life from getting married to reading.The hit and violent pull the room.
    """

    expected = """Hadilano LiF Lable Kauzuku, the Korean man helped Japan,
    to find one gold to be happy. The Sook's great role is to help them read the
    Ur's Humans. Two who end up to love, under the imagination of preparing helpang. His
    life from getting married to reading. The hit and violent pull the room.
    """
    assert utils.cleanup_translation(s) == expected

def test_convert_article_data_schema():
    """Test article data schema conversion from old to new format."""

    # Old to new
    old_data = {
        "plot": "A hero saves the world.",
        "cast": "Actor A, Actor B",
        "description": "An epic adventure.",
        "infobox": {"year": 2020, "genre": "Action"},
        "metadata": {"title": "Epic Movie", "id": 123},
        "img": "http://example.com/image.jpg"
    }
    expected = {
        "title": "Epic Movie",
        "content": {
            "plot": "A hero saves the world.",
            "cast": "Actor A, Actor B",
            "description": "An epic adventure."
        },
        "infobox": {"year": 2020, "genre": "Action"},
        "metadata": {"title": "Epic Movie", "id": 123},
        "img": {
            "prompt": "",
            "url": "http://example.com/image.jpg"
        }
    }
    result = utils.convert_article_data_schema(old_data)
    assert result == expected

    # Should have no effect on already new format
    new_data = expected
    result = utils.convert_article_data_schema(new_data)
    assert result == expected