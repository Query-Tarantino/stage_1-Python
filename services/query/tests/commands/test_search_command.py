from pathlib import Path
from typing import Dict, List, Optional, Set

from tarantino_query.commands.search_command import SearchCommand
from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.ports.inverted_index_reader import InvertedIndexReader
from tarantino_query.ports.metadata_reader import MetadataReader


class InMemoryIndex(InvertedIndexReader):
    def __init__(self, postings: Dict[str, Set[int]]):
        self._postings = postings

    def postings(self, term: str) -> Set[int]:
        return self._postings.get(term, set())


class InMemoryMetadata(MetadataReader):
    def book(self, book_id: int) -> Optional[BookMetadata]:
        return BookMetadata(book_id, "Title", "Author", "English", Path("body.txt"))

    def books_by(self, author: str) -> List[BookMetadata]:
        return []


def test_returns_the_books_ordered_by_id():
    index = InMemoryIndex({"island": {64317, 1342, 84}, "whale": {84, 1342, 64317, 5}})
    search = SearchCommand(index, InMemoryMetadata(), set())

    result = search.execute("island whale")

    assert [book.book_id for book in result.books] == [84, 1342, 64317]
