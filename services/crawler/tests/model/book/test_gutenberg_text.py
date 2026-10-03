import pytest

from tarantino_crawler.model.book.gutenberg_text import GutenbergText
from tarantino_crawler.model.failure.download_exception import DownloadException

RAW = "Title: Pride and Prejudice\r\nAuthor: Jane Austen\r\n\r\n*** START OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***\r\n\r\nIt is a truth universally acknowledged.\r\n\r\n*** END OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***\r\nLicense text.\r\n"


def test_splits_header_and_body_discarding_markers_and_footer():
    text = GutenbergText.book_text(1, RAW)
    assert text.header == "Title: Pride and Prejudice\nAuthor: Jane Austen"
    assert text.body == "It is a truth universally acknowledged."


def test_accepts_legacy_this_markers():
    raw_legacy = "Title: A\n*** START OF THIS PROJECT GUTENBERG EBOOK A ***\nBody\n*** END OF THIS PROJECT GUTENBERG EBOOK A ***\n"
    text = GutenbergText.book_text(1, raw_legacy)
    assert text.header == "Title: A"
    assert text.body == "Body"


def test_fails_when_markers_are_missing():
    with pytest.raises(DownloadException):
        GutenbergText.book_text(1, "No markers here")
