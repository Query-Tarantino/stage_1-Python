from __future__ import annotations

from typing import Protocol

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


class InvertedIndexStorage(Protocol):
    def open(self) -> None:
        """Loads from storage whatever the structure keeps in memory, before the first
        book is added. Adding loads it anyway; opening first lets the cost of loading be
        paid, or measured, apart from indexing."""

    def add(self, occurrences: TermOccurrences) -> None: ...

    def flush(self) -> None: ...
