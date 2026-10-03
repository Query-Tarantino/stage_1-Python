from functools import reduce
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

    def _books_containing_all(self, terms: Set[str]) -> List[BookMetadata]:
        ids = self._ids_containing_all(terms)
        books = []
        for book_id in sorted(ids):
            book = self.metadata.book(book_id)
            if book is not None:
                books.append(book)
        return books

    def _ids_containing_all(self, terms: Set[str]) -> Set[int]:
        if not terms:
            return set()

        sets = [self.inverted_index.postings(term) for term in terms]
        return reduce(lambda x, y: x.intersection(y), sets)
