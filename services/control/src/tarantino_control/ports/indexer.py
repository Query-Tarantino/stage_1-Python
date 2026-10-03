from __future__ import annotations

from typing import Dict, List, Protocol

from tarantino_control.model.outcome import Outcome


class Indexer(Protocol):
    def index(self, book_ids: List[int]) -> Dict[int, Outcome]:
        """Indexes the books together, flushing the index once, and returns the outcome
        of each one by id."""
        ...
