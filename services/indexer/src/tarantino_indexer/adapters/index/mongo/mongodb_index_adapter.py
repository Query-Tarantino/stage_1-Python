from __future__ import annotations

from collections import defaultdict
from typing import Dict, Set

from pymongo import MongoClient

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)


class MongodbIndexAdapter(InvertedIndexStorage):
    def __init__(self, uri: str):
        self.uri = uri
        self.client = MongoClient(uri)
        self.collection = self.client["tarantino"]["inverted_index"]
        self._memory: Dict[str, Set[int]] = defaultdict(set)

    def add(self, occurrences: TermOccurrences) -> None:
        for term in occurrences.frequencies.keys():
            self._memory[term].add(occurrences.book_id)

    def flush(self) -> None:
        if not self._memory:
            return

        for term, book_ids in self._memory.items():
            self.collection.update_one(
                {"_id": term},
                {"$addToSet": {"postings": {"$each": sorted(book_ids)}}},
                upsert=True,
            )

        self._memory.clear()
