from pathlib import Path

from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.model.book.header_parser import HeaderParser


def test_extracts_title_author_and_language():
    header = "Title: Robinson Crusoe\nAuthor: Daniel Defoe\nOther: Something\nLanguage: English"
    body_path = Path("fake/path")
    book = HeaderParser().book(BookText(5, header, "", body_path))

    assert book.book_id == 5
    assert book.title == "Robinson Crusoe"
    assert book.author == "Daniel Defoe"
    assert book.language == "English"
    assert book.path == body_path


def test_leaves_missing_fields_as_null():
    header = "Title: Only a title"
    body_path = Path("fake/path")
    book = HeaderParser().book(BookText(6, header, "", body_path))

    assert book.book_id == 6
    assert book.title == "Only a title"
    assert book.author is None
    assert book.language is None
    assert book.path == body_path
