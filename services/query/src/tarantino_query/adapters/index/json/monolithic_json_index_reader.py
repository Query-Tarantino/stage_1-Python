import json
from pathlib import Path
from typing import Dict, Optional, Set

from tarantino_query.ports.inverted_index_reader import InvertedIndexReader


class MonolithicJsonIndexReader(InvertedIndexReader):
    def __init__(self, file: Path):
        self.file = file
        self._index: Optional[Dict[str, Set[int]]] = None

    def postings(self, term: str) -> Set[int]:
        return self._get_index().get(term, set())

    def _get_index(self) -> Dict[str, Set[int]]:
        if self._index is None:
            self._index = self._stored_index() if self.file.exists() else {}
        return self._index

    def _stored_index(self) -> Dict[str, Set[int]]:
        with open(self.file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: set(v) for k, v in data.items()}
