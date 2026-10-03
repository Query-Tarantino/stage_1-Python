from __future__ import annotations

from concurrent.futures import Future
from typing import Protocol

from tarantino_control.model.outcome import Outcome


class Download(Protocol):
    # A finished download, or a book already in the datalake, waiting to be stored
    def store(self) -> Outcome: ...


class Crawler(Protocol):
    def ingest(self, book_id: int) -> Future[Download]:
        """Starts ingesting a book (SPEC §9): a book the datalake already holds is not
        downloaded again, and any other is downloaded in the background, several at
        once, without writing anything. Once the download finishes, the caller stores it
        with Download.store(), so only the caller's thread uses the datalake."""
        ...
