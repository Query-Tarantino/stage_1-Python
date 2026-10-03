from typing import Set

from pymongo import MongoClient

from tarantino_query.ports.inverted_index_reader import InvertedIndexReader


class MongodbIndexReader(InvertedIndexReader):
    def __init__(self, uri: str):
        self.uri = uri
        self.client = MongoClient(uri)
        self.collection = self.client["tarantino"]["inverted_index"]

    def postings(self, term: str) -> Set[int]:
        doc = self.collection.find_one({"_id": term})
        if doc and "postings" in doc:
            return set(doc["postings"])
        return set()
