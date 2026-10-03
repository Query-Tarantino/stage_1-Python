from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional, Set

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)


class MonolithicJsonIndexAdapter(InvertedIndexStorage):
    def __init__(self, file: Path):
        self.file = file
        self._index_cache: Optional[Dict[str, Set[int]]] = None

    def open(self) -> None:
        self._index()

    def add(self, occurrences: TermOccurrences) -> None:
        for term in occurrences.frequencies.keys():
            self._postings(term).add(occurrences.book_id)

    def flush(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self._write_atomically()

    def _postings(self, term: str) -> Set[int]:
        idx = self._index()
        if term not in idx:
            idx[term] = set()
        return idx[term]

    def _index(self) -> Dict[str, Set[int]]:
        if self._index_cache is None:
            self._index_cache = self._stored_index() if self.file.exists() else {}
        return self._index_cache

    def _stored_index(self) -> Dict[str, Set[int]]:
        data = json.loads(self.file.read_text(encoding="utf-8"))
        return {term: set(ids) for term, ids in data.items()}

    def _write_atomically(self) -> None:
        tmp = self.file.with_name(self.file.name + ".tmp")
        data_to_write = {
            term: sorted(ids) for term, ids in sorted(self._index().items())
        }
        content = json.dumps(data_to_write, ensure_ascii=False, separators=(",", ":"))
        tmp.write_text(content, encoding="utf-8", newline="\n")
        os.replace(tmp, self.file)
