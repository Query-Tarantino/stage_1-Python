from pathlib import Path

from tarantino_indexer.adapters.datalake.batch.batch_based_datalake_reader import (
    BatchBasedDatalakeReader,
)
from tarantino_indexer.adapters.datalake.book.book_based_datalake_reader import (
    BookBasedDatalakeReader,
)
from tarantino_indexer.adapters.datalake.time.time_based_datalake_reader import (
    TimeBasedDatalakeReader,
)
from tarantino_indexer.model.book.book_text import BookText


def store(root: Path, relative: str, content: bytes) -> Path:
    file = root / relative
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(content)
    return file


def test_reads_every_layout(tmp_path):
    for header, body in [
        ("20250925/14/5.header.txt", "20250925/14/5.body.txt"),
        ("1342/header.txt", "1342/body.txt"),
        ("64/64317.header.txt", "64/64317.body.txt"),
    ]:
        store(tmp_path, header, b"header")
        store(tmp_path, body, b"body")

    assert TimeBasedDatalakeReader(tmp_path).book_text(5) == BookText(
        5, "header", "body", tmp_path / "20250925/14/5.body.txt"
    )
    assert BookBasedDatalakeReader(tmp_path).book_text(1342) == BookText(
        1342, "header", "body", tmp_path / "1342/body.txt"
    )
    assert BatchBasedDatalakeReader(tmp_path).book_text(64317) == BookText(
        64317, "header", "body", tmp_path / "64/64317.body.txt"
    )


def test_ignores_books_without_body(tmp_path):
    store(tmp_path, "7/header.txt", b"header")

    assert BookBasedDatalakeReader(tmp_path).book_text(7) is None
    assert TimeBasedDatalakeReader(tmp_path / "missing").book_text(7) is None


def test_reads_the_files_exactly_as_written(tmp_path):
    store(tmp_path, "1/header.txt", "Title: A\rB\u2028C\r\n".encode("utf-8"))
    store(tmp_path, "1/body.txt", "one\r\ntwo\rthree".encode("utf-8"))

    text = BookBasedDatalakeReader(tmp_path).book_text(1)

    assert text.header == "Title: A\rB\u2028C\r\n"
    assert text.body == "one\r\ntwo\rthree"


def test_looks_time_books_up_no_deeper_than_the_hour_directories(tmp_path):
    store(tmp_path, "20250925/14/extra/5.header.txt", b"header")
    store(tmp_path, "20250925/14/extra/5.body.txt", b"body")

    assert TimeBasedDatalakeReader(tmp_path).book_text(5) is None
