from __future__ import annotations

from typing import Protocol

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


class InvertedIndexStorage(Protocol):
    def add(self, occurrences: TermOccurrences) -> None: ...

    def flush(self) -> None: ...
