from typing import Dict, List

from tarantino_control.adapters.local_crawler import LocalCrawler
from tarantino_control.adapters.local_indexer import LocalIndexer
from tarantino_control.model.outcome import Outcome
from tarantino_crawler.adapters.datalake.book.book_based_datalake_adapter import (
    BookBasedDatalakeAdapter,
)
from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason
from tarantino_crawler.ports.book_downloader import BookDownloader
from tarantino_indexer.commands.index_result import IndexResult

TEXT = (
    "Title: A\n*** START OF THE PROJECT GUTENBERG EBOOK A ***\n"
    "Body\n*** END OF THE PROJECT GUTENBERG EBOOK A ***"
)


class Mirror(BookDownloader):
    def __init__(self, books: Dict[int, str]):
        self._books = books

    def raw_text(self, book_id: int) -> str:
        if book_id not in self._books:
            raise DownloadException(
                FailureReason.NOT_FOUND, f"Book {book_id} not found"
            )
        return self._books[book_id]


def test_local_crawler_reports_the_directory_of_a_stored_book(tmp_path):
    crawler = LocalCrawler(
        IngestBookCommand(Mirror({1342: TEXT}), BookBasedDatalakeAdapter(tmp_path))
    )

    assert crawler.ingest(1342) == Outcome.success(f"stored in {tmp_path / '1342'}")


def test_local_crawler_reports_the_failure_reason_of_a_skipped_book(tmp_path):
    crawler = LocalCrawler(
        IngestBookCommand(Mirror({}), BookBasedDatalakeAdapter(tmp_path))
    )

    assert crawler.ingest(84) == Outcome.failure("skipped, NOT_FOUND")


class IndexCommand:
    def __init__(self, results: Dict[int, IndexResult]):
        self._results = results
        self.batches: List[List[int]] = []

    def execute(self, book_ids: List[int]) -> List[IndexResult]:
        self.batches.append(book_ids)
        return [self._results[book_id] for book_id in book_ids]


def test_local_indexer_reports_the_terms_indexed_of_a_book():
    command = IndexCommand({1342: IndexResult.success(1342, 7012)})

    assert LocalIndexer(command).index(1342) == Outcome.success(
        "7012 unique terms indexed"
    )
    assert command.batches == [[1342]]


def test_local_indexer_reports_a_book_missing_from_the_datalake():
    command = IndexCommand({84: IndexResult.not_found(84)})

    assert LocalIndexer(command).index(84) == Outcome.failure(
        "skipped, not found in the datalake"
    )
