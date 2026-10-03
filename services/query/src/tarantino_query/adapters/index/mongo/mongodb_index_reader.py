from typing import Set

from tarantino_query.adapters.mongo.mongo_databases import MongoDatabases
from tarantino_query.ports.inverted_index_reader import InvertedIndexReader


class MongodbIndexReader(InvertedIndexReader):
    COLLECTION = "inverted_index"

    def __init__(self, uri: str):
        self._collection = MongoDatabases.database(uri)[self.COLLECTION]

    def postings(self, term: str) -> Set[int]:
        # One find by term on every lookup, reading the whole document (SPEC §8.1)
        document = self._collection.find_one({"term": term})
        return set(document["postings"]) if document else set()
