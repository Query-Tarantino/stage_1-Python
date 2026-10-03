from pathlib import Path

from tarantino_query.__main__ import line
from tarantino_query.model.book_metadata import BookMetadata


def test_prints_each_book_with_its_metadata():
    path = Path("datalake/1342/body.txt")
    book = BookMetadata(1342, "Pride and Prejudice", "Jane Austen", "English", path)

    assert line(book) == f"  [1342] Pride and Prejudice — Jane Austen (English) {path}"


def test_writes_missing_fields_as_null():
    path = Path("datalake/2/body.txt")
    book = BookMetadata(2, "No Author Here", None, None, path)

    assert line(book) == f"  [2] No Author Here — null (null) {path}"
