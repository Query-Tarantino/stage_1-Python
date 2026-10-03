from __future__ import annotations

from pymongo import UpdateOne

from tarantino_indexer.adapters.index.pending_postings import PendingPostings
from tarantino_indexer.adapters.mongo.mongo_databases import MongoDatabases
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)


class MongodbIndexAdapter(InvertedIndexStorage):
    COLLECTION = "inverted_index"

    def __init__(self, uri: str):
        self._collection = MongoDatabases.database(uri)[self.COLLECTION]
        self._collection.create_index("term", unique=True)
        self._pending = PendingPostings()

    def add(self, occurrences: TermOccurrences) -> None:
        self._pending.add(occurrences)

    def flush(self) -> None:
        # One unordered bulk write with an upsert per affected term, in term order; the
        # driver splits it into batches of the server's limit (SPEC §8.1)
        updates = [
            UpdateOne(
                {"term": term},
                {"$addToSet": {"postings": {"$each": sorted(ids)}}},
                upsert=True,
            )
            for term, ids in self._pending.drain()
        ]
        if updates:
            self._collection.bulk_write(updates, ordered=False)
