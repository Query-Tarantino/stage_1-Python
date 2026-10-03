from dataclasses import dataclass
from typing import List

from tarantino_query.model.book_metadata import BookMetadata


@dataclass(frozen=True)
class SearchResult:
    query: str
    books: List[BookMetadata]
