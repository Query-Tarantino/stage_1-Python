from __future__ import annotations

from typing import Protocol

from tarantino_control.model.outcome import Outcome


class Indexer(Protocol):
    def index(self, book_id: int) -> Outcome: ...
