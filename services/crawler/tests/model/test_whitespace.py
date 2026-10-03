import sys

from tarantino_crawler.model.whitespace import JAVA_WHITESPACE


def test_is_python_whitespace_without_the_four_characters_java_strip_keeps():
    python_whitespace = {chr(c) for c in range(sys.maxunicode + 1) if chr(c).isspace()}

    assert set(JAVA_WHITESPACE) == python_whitespace - {
        "\u0085",
        "\u00a0",
        "\u2007",
        "\u202f",
    }
