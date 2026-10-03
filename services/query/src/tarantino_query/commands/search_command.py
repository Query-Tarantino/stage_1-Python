from functools import reduce
from operator import iand
from typing import List, Set

from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.model.query_terms import QueryTerms
from tarantino_query.model.search_result import SearchResult
from tarantino_query.ports.inverted_index_reader import InvertedIndexReader
from tarantino_query.ports.metadata_reader import MetadataReader


class SearchCommand:
    def __init__(
        self,
        inverted_index: InvertedIndexReader,
        metadata: MetadataReader,
        stopwords: Set[str],
    ):
        self.inverted_index = inverted_index
        self.metadata = metadata
        self.stopwords = stopwords

    def execute(self, query: str) -> SearchResult:
        terms = QueryTerms.of(query, self.stopwords)
        return SearchResult(query, self._books_containing_all(terms))

    def _books_containing_all(self, terms: List[str]) -> List[BookMetadata]:
        books = []
        for book_id in self._ids_containing_all(terms):
            book = self.metadata.book(book_id)
            if book is not None:
                books.append(book)
        return books

    def _ids_containing_all(self, terms: List[str]) -> List[int]:
        if not terms:
            return []

        sets = (set(self.inverted_index.postings(term)) for term in terms)
        return sorted(reduce(iand, sets))
