from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Set

from tarantino_crawler.model.book.gutenberg_text import GutenbergText
from tarantino_indexer.adapters.stopwords.file_stopwords_loader import (
    FileStopwordsLoader,
)
from tarantino_indexer.model.book.book import Book
from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.model.book.header_parser import HeaderParser
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences
from tarantino_indexer.model.terms.tokenizer import Tokenizer
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage

from services.crawler.tests.benchmarking.support.dataset.benchmark_dataset import (
    BenchmarkDataset,
)
from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)


class IndexFixture:
    # Books of the cache read, split, tokenized and indexed as the indexer does, without
    # a datalake in between (SPEC §11)

    def __init__(self, dataset: BenchmarkDataset, tokenizer: Tokenizer):
        self.dataset = dataset
        self._tokenizer = tokenizer
        self._header_parser = HeaderParser()

    @staticmethod
    def from_environment() -> IndexFixture:
        stopwords = BenchmarkPaths.workload() / "stopwords.txt"
        return IndexFixture(
            BenchmarkDataset.from_environment(),
            Tokenizer(FileStopwordsLoader(stopwords).stopwords()),
        )

    def index(self, inverted_index: InvertedIndexStorage, ids: Sequence[int]) -> None:
        self.add(inverted_index, ids)
        inverted_index.flush()

    def add(self, inverted_index: InvertedIndexStorage, ids: Sequence[int]) -> None:
        for book_id in ids:
            inverted_index.add(self._occurrences(book_id))

    @staticmethod
    def save(metadata: MetadataStorage, books: Sequence[Book]) -> None:
        for book in books:
            metadata.save(book)

    def books(self, ids: Sequence[int]) -> List[Book]:
        return [self._header_parser.book(self._book_text(book_id)) for book_id in ids]

    def vocabulary_size(self, ids: Sequence[int]) -> int:
        # Distinct terms of the books, which every index structure must hold once
        # they are indexed
        vocabulary: Set[str] = set()
        for book_id in ids:
            vocabulary |= self.terms(book_id)
        return len(vocabulary)

    def terms(self, book_id: int) -> Set[str]:
        return set(self._occurrences(book_id).frequencies)

    def _occurrences(self, book_id: int) -> TermOccurrences:
        return self._tokenizer.occurrences(book_id, self._book_text(book_id).body)

    def _book_text(self, book_id: int) -> BookText:
        split = GutenbergText.book_text(book_id, self.dataset.raw_text(book_id))
        return BookText(
            book_id, split.header, split.body, Path("datalake", f"{book_id}.body.txt")
        )
