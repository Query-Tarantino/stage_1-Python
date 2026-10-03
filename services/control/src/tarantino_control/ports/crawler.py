from __future__ import annotations

from typing import Protocol

from tarantino_control.model.outcome import Outcome


class Crawler(Protocol):
    def ingest(self, book_id: int) -> Outcome: ...
