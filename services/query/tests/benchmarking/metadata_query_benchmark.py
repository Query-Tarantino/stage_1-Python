from __future__ import annotations

import random
from typing import List, Optional

from tarantino_indexer.model.book.book import Book
from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.query_config import QueryConfig
from tarantino_query.query_factory import QueryFactory

from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    timed_operation,
)
from services.crawler.tests.benchmarking.support.harness.iterations import (
    MICROSECONDS,
)
from services.crawler.tests.benchmarking.support.validation.check import Check
from services.indexer.tests.benchmarking.support.benchmark_store import BenchmarkStore
from services.indexer.tests.benchmarking.support.index_fixture import IndexFixture


class MetadataQueryBenchmark(Benchmark):
    STRUCTURES = ("sqlite", "mongo")

    def setup_trial(self) -> None:
        self._store = BenchmarkStore.for_metadata(
            self.structure, f"query-metadata-{self.structure}-{self.books}"
        )
        self._store.clear()
        fixture = IndexFixture.from_environment()
        self._ids = fixture.dataset.ids(self.books)
        books = fixture.books(self._ids)
        fixture.save(self._store.metadata(), books)
        # The distinct authors of the dataset, leaving out books without one, so that
        # prolific authors are not favoured (SPEC §11)
        self._authors = list(
            dict.fromkeys(book.author for book in books if book.author is not None)
        )
        self._reader = QueryFactory.metadata(
            QueryConfig(
                self._store.datamarts,
                "json",
                self.structure,
                self._store.mongo_uri,
                BenchmarkPaths.workload(),
            )
        )
        for book_id in self._ids:
            self._require_book(book_id)
        for book in books:
            if book.author is not None:
                self._require_among_books_of_its_author(book)

    @timed_operation(MICROSECONDS)
    def book_by_id_time(self) -> Optional[BookMetadata]:
        return self._reader.book(self._ids[random.randrange(len(self._ids))])

    @timed_operation(MICROSECONDS)
    def books_by_author_time(self) -> List[BookMetadata]:
        return self._reader.books_by(
            self._authors[random.randrange(len(self._authors))]
        )

    def teardown_trial(self) -> None:
        self._store.clear()

    def _require_book(self, book_id: int) -> None:
        book = self._reader.book(book_id)
        Check.require(
            book is not None and book.book_id == book_id, f"book {book_id} not found"
        )

    def _require_among_books_of_its_author(self, book: Book) -> None:
        found = any(
            candidate.book_id == book.book_id
            for candidate in self._reader.books_by(book.author)
        )
        Check.require(
            found, f"book {book.book_id} missing from the books of its author"
        )
