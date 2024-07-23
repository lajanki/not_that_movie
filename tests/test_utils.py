import pytest

from src import (
	utils
)



def test_format_as_html():
    """Test html formatting of parsed content."""
    description = {
        "plot": "one\n\ntwo\n\nthree\n\nfour.",
        "cast": "James as lion\nJohn as submarine"
    }

    formatted = {
        "plot": "<p>one</p><p>two</p><p>three</p><p>four.</p>",
        "cast": "<ul><li>James as lion</li><li>John as submarine</li></ul>",
        "description": ""
    }

    assert utils.format_as_html(description) == formatted

@pytest.mark.parametrize(
    "test_string,expected",
    [
        ("Budget: $ 45 million", "Budget: $45 million"),
        ("one two.Skidoo", "one two. Skidoo"),
        ("one two.three", "one two.three")
    ])
def test_cleanup_translation(test_string, expected):
    """Test translation generated common tokens."""
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
