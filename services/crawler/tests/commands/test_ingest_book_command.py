from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set

from tarantino_crawler.commands.download_result import DownloadResult
from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.commands.ingest_result import IngestResult
from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason
from tarantino_crawler.ports.book_downloader import BookDownloader
from tarantino_crawler.ports.datalake_storage import DatalakeStorage

RAW = (
    "Title: T\n*** START OF THE PROJECT GUTENBERG EBOOK T ***\n"
    "body\n*** END OF THE PROJECT GUTENBERG EBOOK T ***"
)


class Texts(BookDownloader):
    def __init__(self, text: str):
        self._text = text

    def raw_text(self, book_id: int) -> str:
        return self._text


class Missing(BookDownloader):
    def raw_text(self, book_id: int) -> str:
        raise DownloadException(FailureReason.NOT_FOUND, "missing")


class Unreachable(BookDownloader):
    def raw_text(self, book_id: int) -> str:
        raise AssertionError(f"Book {book_id} must not be downloaded")


class InMemoryDatalake(DatalakeStorage):
    def __init__(self):
        self.books: Dict[int, BookText] = {}

    @staticmethod
    def paths(book_id: int) -> StoredPaths:
        return StoredPaths(Path(f"{book_id}.header.txt"), Path(f"{book_id}.body.txt"))

    def save(self, book: BookText) -> StoredPaths:
        self.books[book.book_id] = book
        return self.paths(book.book_id)

    def paths_of(self, book_id: int) -> Optional[StoredPaths]:
        return self.paths(book_id) if book_id in self.books else None

    def ids_stored_since(self, instant: datetime) -> Set[int]:
        return set(self.books)

    def remove_incomplete_writes(self) -> int:
        return 0


class FullDisk(InMemoryDatalake):
    def save(self, book: BookText) -> StoredPaths:
        raise OSError("disk full")


def test_downloads_splits_and_stores_new_books():
    datalake = InMemoryDatalake()

    assert IngestBookCommand(Texts(RAW), datalake).execute(5) == IngestResult.success(
        5, InMemoryDatalake.paths(5)
    )
    assert datalake.books[5] == BookText(5, "Title: T", "body")


def test_reuses_books_already_in_the_datalake_without_downloading():
    datalake = InMemoryDatalake()
    datalake.save(BookText(5, "header", "body"))

    assert IngestBookCommand(Unreachable(), datalake).execute(
        5
    ) == IngestResult.success(5, InMemoryDatalake.paths(5))


def test_reports_download_failures_without_storing():
    datalake = InMemoryDatalake()

    result = IngestBookCommand(Missing(), datalake).execute(5)

    assert result == IngestResult.failure_result(5, FailureReason.NOT_FOUND)
    assert 5 not in datalake.books


def test_reports_books_without_markers_as_missing_markers():
    result = IngestBookCommand(Texts("no markers"), InMemoryDatalake()).execute(5)

    assert result == IngestResult.failure_result(5, FailureReason.MISSING_MARKERS)


def test_downloads_without_writing_the_datalake_until_the_book_is_stored():
    datalake = InMemoryDatalake()
    ingest = IngestBookCommand(Texts(RAW), datalake)

    download = ingest.download(5)

    assert download == DownloadResult.success(BookText(5, "Title: T", "body"))
    assert 5 not in datalake.books
    assert ingest.store(download) == IngestResult.success(5, InMemoryDatalake.paths(5))
    assert datalake.books[5] == BookText(5, "Title: T", "body")


def test_stores_nothing_for_a_failed_download():
    datalake = InMemoryDatalake()
    failed = DownloadResult.failure_result(5, FailureReason.NETWORK_ERROR)

    result = IngestBookCommand(Unreachable(), datalake).store(failed)

    assert result == IngestResult.failure_result(5, FailureReason.NETWORK_ERROR)
    assert 5 not in datalake.books


def test_reports_storage_errors():
    result = IngestBookCommand(Texts(RAW), FullDisk()).execute(5)

    assert result == IngestResult.failure_result(5, FailureReason.STORAGE_ERROR)
