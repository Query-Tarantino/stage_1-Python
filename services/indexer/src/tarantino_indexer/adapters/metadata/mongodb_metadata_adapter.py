from __future__ import annotations

from tarantino_indexer.adapters.mongo.mongo_databases import MongoDatabases
from tarantino_indexer.model.book.book import Book
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage


class MongodbMetadataAdapter(MetadataStorage):
    COLLECTION = "books"

    def __init__(self, uri: str):
        self._collection = MongoDatabases.database(uri)[self.COLLECTION]
        self._collection.create_index("book_id", unique=True)

    def save(self, book: Book) -> None:
        # One replaceOne by book_id, upserted; missing fields are null (SPEC §8.2)
        self._collection.replace_one(
            {"book_id": book.book_id}, self._document(book), upsert=True
        )

    @staticmethod
    def _document(book: Book) -> dict:
        return {
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "language": book.language,
            "path": book.path.as_posix(),
        }
