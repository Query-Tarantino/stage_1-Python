from pathlib import Path

import pytest

from tarantino_crawler.adapters.gutenberg.local_mirror_downloader import (
    LocalMirrorDownloader,
)
from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason


def write(mirror: Path, relative: str, content: bytes) -> None:
    file = mirror / relative
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(content)


def failure(mirror: Path, book_id: int) -> FailureReason:
    with pytest.raises(DownloadException) as error:
        LocalMirrorDownloader(mirror).raw_text(book_id)
    return error.value.reason


def test_reads_a_book_from_the_generated_collection_layout(tmp_path):
    write(tmp_path, "1342/pg1342.txt", "Title: Pride and Prejudice — café\r\n".encode())

    text = LocalMirrorDownloader(tmp_path).raw_text(1342)

    assert text == "Title: Pride and Prejudice — café\r\n"


def test_reports_a_book_missing_from_the_mirror_as_not_found(tmp_path):
    assert failure(tmp_path, 84) == FailureReason.NOT_FOUND


def test_reports_a_text_that_is_not_utf8_as_a_network_error(tmp_path):
    write(tmp_path, "84/pg84.txt", b"\xff\xfe broken")

    assert failure(tmp_path, 84) == FailureReason.NETWORK_ERROR


def test_lists_the_books_with_a_text_in_id_order(tmp_path):
    for file in ["1342/pg1342.txt", "84/pg84.txt", "11/pg11-images.epub", "README"]:
        write(tmp_path, file, b"text")
    write(tmp_path, "cache/pgcache.txt", b"text")

    assert LocalMirrorDownloader(tmp_path).book_ids() == [84, 1342]
