from typing import List, Optional, Protocol

from tarantino_query.model.book_metadata import BookMetadata


class MetadataReader(Protocol):
    def book(self, book_id: int) -> Optional[BookMetadata]: ...

    def books_by(self, author: str) -> List[BookMetadata]: ...
