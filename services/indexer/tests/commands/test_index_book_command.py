from pathlib import Path
from typing import Dict, List, Optional

from tarantino_indexer.commands.index_book_command import IndexBookCommand
from tarantino_indexer.commands.index_result import IndexResult
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

BODY = Path("datalake/1342/body.txt")


class StoredBooks(DatalakeReader):
    def __init__(self, texts: Dict[int, BookText]):
        self._texts = texts

    def book_text(self, book_id: int) -> Optional[BookText]:
        return self._texts.get(book_id)


class RecordingIndex(InvertedIndexStorage):
    def __init__(self):
        self.added: List[TermOccurrences] = []
        self.flushes = 0

    def add(self, occurrences: TermOccurrences) -> None:
        self.added.append(occurrences)

    def flush(self) -> None:
        self.flushes += 1


class RecordingMetadata(MetadataStorage):
    def __init__(self):
        self.saved: List[Book] = []

    def save(self, book: Book) -> None:
        self.saved.append(book)


def command(texts: Dict[int, BookText], index, metadata) -> IndexBookCommand:
    return IndexBookCommand(
        StoredBooks(texts), HeaderParser(), Tokenizer({"the"}), index, metadata
    )


def test_saves_metadata_and_flushes_the_terms_of_stored_books():
    text = BookText(
        1342, "Title: Pride\nAuthor: Austen", "The island, the island!", BODY
    )
    index, metadata = RecordingIndex(), RecordingMetadata()

    results = command({1342: text}, index, metadata).execute([1342])

    assert results == [IndexResult.success(1342, 1)]
    assert metadata.saved == [Book(1342, "Pride", "Austen", None, BODY)]
    assert index.added == [TermOccurrences(1342, {"island": 2})]
    assert index.flushes == 1


def test_reports_books_missing_from_the_datalake_without_writing():
    index, metadata = RecordingIndex(), RecordingMetadata()

    assert command({}, index, metadata).execute([7]) == [IndexResult.not_found(7)]
    assert metadata.saved == []
    assert index.added == []


def test_indexes_a_batch_with_one_flush_and_reports_each_book():
    stored = {
        1: BookText(1, "Title: One", "whale", Path("1.body.txt")),
        3: BookText(3, "Title: Three", "island whale", Path("3.body.txt")),
    }
    index, metadata = RecordingIndex(), RecordingMetadata()

    results = command(stored, index, metadata).execute([1, 2, 3])

    assert results == [
        IndexResult.success(1, 1),
        IndexResult.not_found(2),
        IndexResult.success(3, 2),
    ]
    assert [book.book_id for book in metadata.saved] == [1, 3]
    assert index.flushes == 1


def test_does_not_flush_when_no_book_of_the_batch_is_found():
    index = RecordingIndex()

    command({}, index, RecordingMetadata()).execute([7, 8])

    assert index.flushes == 0
