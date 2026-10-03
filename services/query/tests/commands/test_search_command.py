from pathlib import Path
from typing import Dict, List, Optional, Set

from tarantino_query.commands.search_command import SearchCommand
from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.ports.inverted_index_reader import InvertedIndexReader
from tarantino_query.ports.metadata_reader import MetadataReader


class InMemoryIndex(InvertedIndexReader):
    def __init__(self, postings: Dict[str, Set[int]]):
        self._postings = postings
        self.looked_up: List[str] = []

    def postings(self, term: str) -> Set[int]:
        self.looked_up.append(term)
        return self._postings.get(term, set())


class InMemoryMetadata(MetadataReader):
    def book(self, book_id: int) -> Optional[BookMetadata]:
        if book_id == 999:
            return None
        return BookMetadata(book_id, "Title", "Author", "English", Path("body.txt"))

    def books_by(self, author: str) -> List[BookMetadata]:
        return []


def ids(search: SearchCommand, query: str) -> List[int]:
    return [book.book_id for book in search.execute(query).books]


def test_returns_the_books_ordered_by_id():
    index = InMemoryIndex({"island": {64317, 1342, 84}, "whale": {84, 1342, 64317, 5}})
    search = SearchCommand(index, InMemoryMetadata(), set())

    assert ids(search, "island whale") == [84, 1342, 64317]


def test_returns_nothing_when_a_term_is_unknown():
    search = SearchCommand(InMemoryIndex({"island": {5}}), InMemoryMetadata(), set())

    assert ids(search, "island unicorn") == []


def test_returns_nothing_when_only_stopwords_remain():
    search = SearchCommand(InMemoryIndex({"the": {5}}), InMemoryMetadata(), {"the"})

    assert ids(search, "the a") == []


def test_drops_books_without_metadata():
    search = SearchCommand(
        InMemoryIndex({"ghost": {999, 5}}), InMemoryMetadata(), set()
    )

    assert ids(search, "ghost") == [5]


def test_looks_every_term_up_in_query_order_even_once_nothing_is_left():
    index = InMemoryIndex({"whale": {5}, "island": {84}, "ship": {5, 84}})
    search = SearchCommand(index, InMemoryMetadata(), set())

    search.execute("whale island ship whale")

    assert index.looked_up == ["whale", "island", "ship"]


def test_leaves_the_postings_of_the_index_unchanged():
    stored = {"island": {5, 84, 1342}, "whale": {84}}
    search = SearchCommand(InMemoryIndex(stored), InMemoryMetadata(), set())

    search.execute("island whale")

    assert stored == {"island": {5, 84, 1342}, "whale": {84}}
