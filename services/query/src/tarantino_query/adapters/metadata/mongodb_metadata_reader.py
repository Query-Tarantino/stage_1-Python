from pathlib import Path
from typing import List, Optional

from pymongo import MongoClient

from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.ports.metadata_reader import MetadataReader


class MongodbMetadataReader(MetadataReader):
    def __init__(self, uri: str):
        self.uri = uri
        self.client = MongoClient(uri)
        self.collection = self.client["tarantino"]["metadata"]

    def _to_book_metadata(self, doc: dict) -> BookMetadata:
        return BookMetadata(
            book_id=doc["_id"],
            title=doc.get("title", ""),
            author=doc.get("author", ""),
            language=doc.get("language", ""),
            path=Path(doc.get("path", "")) if doc.get("path") else Path(),
        )

    def book(self, book_id: int) -> Optional[BookMetadata]:
        doc = self.collection.find_one({"_id": book_id})
        if doc:
            return self._to_book_metadata(doc)
        return None

    def books_by(self, author: str) -> List[BookMetadata]:
        docs = self.collection.find({"author": author})
        return [self._to_book_metadata(doc) for doc in docs]
