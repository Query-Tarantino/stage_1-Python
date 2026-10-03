from __future__ import annotations

from pymongo import MongoClient

from tarantino_indexer.model.book.book import Book
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage


class MongodbMetadataAdapter(MetadataStorage):
    def __init__(self, uri: str):
        self.uri = uri
        self.client = MongoClient(uri)
        self.collection = self.client["tarantino"]["metadata"]

    def save(self, book: Book) -> None:
        self.collection.update_one(
            {"_id": book.book_id},
            {
                "$set": {
                    "title": book.title,
                    "author": book.author,
                    "language": book.language,
                    "path": book.path.as_posix() if book.path else None,
                }
            },
            upsert=True,
        )
