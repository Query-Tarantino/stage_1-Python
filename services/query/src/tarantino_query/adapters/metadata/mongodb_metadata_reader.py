import re
from pathlib import Path
from typing import List, Optional

from pymongo import ASCENDING

from tarantino_query.adapters.mongo.mongo_databases import MongoDatabases
from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.ports.metadata_reader import MetadataReader


class MongodbMetadataReader(MetadataReader):
    COLLECTION = "books"

    def __init__(self, uri: str):
        self._collection = MongoDatabases.database(uri)[self.COLLECTION]

    def book(self, book_id: int) -> Optional[BookMetadata]:
        document = self._collection.find_one({"book_id": book_id})
        return self._book(document) if document else None

    def books_by(self, author: str) -> List[BookMetadata]:
        documents = self._collection.find(
            {"author": {"$regex": re.escape(author), "$options": "i"}}
        ).sort("book_id", ASCENDING)
        return [self._book(document) for document in documents]

    @staticmethod
    def _book(document: dict) -> BookMetadata:
        return BookMetadata(
            document["book_id"],
            document.get("title"),
            document.get("author"),
            document.get("language"),
            Path(document["path"]),
        )
