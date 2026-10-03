from concurrent.futures import Executor, Future
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from tarantino_control.adapters.local_crawler import LocalCrawler
from tarantino_control.adapters.local_indexer import LocalIndexer
from tarantino_control.model.outcome import Outcome
from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.model.book.book_text import BookText as CrawledText
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason
from tarantino_crawler.ports.book_downloader import BookDownloader
from tarantino_crawler.ports.datalake_storage import DatalakeStorage
from tarantino_indexer.commands.index_book_command import IndexBookCommand
from tarantino_indexer.model.book.book import Book
from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.model.book.header_parser import HeaderParser
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences
from tarantino_indexer.model.terms.tokenizer import Tokenizer
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage
from tarantino_indexer.ports.sources.datalake_reader import DatalakeReader

RAW = (
    "Title: T\n*** START OF THE PROJECT GUTENBERG EBOOK T ***\n"
    "body\n*** END OF THE PROJECT GUTENBERG EBOOK T ***"
)


class Texts(BookDownloader):
    def raw_text(self, book_id: int) -> str:
        return RAW


class Missing(BookDownloader):
    def raw_text(self, book_id: int) -> str:
        raise DownloadException(FailureReason.NOT_FOUND, "missing")


class Unreachable(BookDownloader):
    def raw_text(self, book_id: int) -> str:
        raise AssertionError(f"Book {book_id} must not be downloaded")


class RecordingDatalake(DatalakeStorage):
    def __init__(self):
        self.books: Dict[int, StoredPaths] = {}
        self.saved: List[int] = []

    def save(self, book: CrawledText) -> StoredPaths:
        directory = Path("datalake", str(book.book_id))
        self.books[book.book_id] = StoredPaths(
            directory / "header.txt", directory / "body.txt"
        )
        self.saved.append(book.book_id)
        return self.books[book.book_id]

    def paths_of(self, book_id: int) -> Optional[StoredPaths]:
        return self.books.get(book_id)

    def ids_stored_since(self, instant: datetime) -> Set[int]:
        return set(self.books)

    def remove_incomplete_writes(self) -> int:
        return 0


class Synchronous(Executor):
    # Runs every download at once, in the caller's thread
    def submit(self, fn, *args, **kwargs) -> Future:
        future = Future()
        future.set_result(fn(*args, **kwargs))
        return future


class Deferred(Executor):
    # Keeps the downloads until run() is called
    def __init__(self):
        self.pending = []

    def submit(self, fn, *args, **kwargs) -> Future:
        future = Future()
        self.pending.append((future, fn, args, kwargs))
        return future

    def run(self) -> None:
        for future, fn, args, kwargs in self.pending:
            future.set_result(fn(*args, **kwargs))


def test_crawler_reports_where_a_book_already_stored_is_without_downloading_it():
    datalake = RecordingDatalake()
    datalake.save(CrawledText(5, "header", "body"))
    crawler = LocalCrawler(IngestBookCommand(Unreachable(), datalake), Synchronous())

    outcome = crawler.ingest(5).result().store()

    assert outcome == Outcome.success(f"stored in {Path('datalake', '5')}")


def test_crawler_downloads_with_its_executor_and_writes_only_when_storing():
    datalake, downloads = RecordingDatalake(), Deferred()
    crawler = LocalCrawler(IngestBookCommand(Texts(), datalake), downloads)

    download = crawler.ingest(5)
    assert not download.done()

    downloads.run()
    assert datalake.saved == []
    assert download.result().store() == Outcome.success(
        f"stored in {Path('datalake', '5')}"
    )
    assert datalake.saved == [5]


def test_crawler_reports_the_failure_reason():
    datalake = RecordingDatalake()
    crawler = LocalCrawler(IngestBookCommand(Missing(), datalake), Synchronous())

    assert crawler.ingest(5).result().store() == Outcome.failure("skipped, NOT_FOUND")
    assert datalake.saved == []


class OnlyBook5(DatalakeReader):
    def book_text(self, book_id: int) -> Optional[BookText]:
        if book_id != 5:
            return None
        return BookText(5, "Title: T", "island whale island", Path("5.body.txt"))


class NoIndex(InvertedIndexStorage):
    def add(self, occurrences: TermOccurrences) -> None:
        pass

    def flush(self) -> None:
        pass


class NoMetadata(MetadataStorage):
    def save(self, book: Book) -> None:
        pass


def test_indexer_reports_the_terms_of_each_book_and_the_missing_ones():
    command = IndexBookCommand(
        OnlyBook5(), HeaderParser(), Tokenizer(set()), NoIndex(), NoMetadata()
    )

    assert LocalIndexer(command).index([5, 6]) == {
        5: Outcome.success("2 unique terms indexed"),
        6: Outcome.failure("skipped, not found in the datalake"),
    }
