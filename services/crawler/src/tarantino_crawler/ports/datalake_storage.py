from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, Set

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths


class DatalakeStorage(Protocol):
    def save(self, book: BookText) -> StoredPaths: ...

    def paths_of(self, book_id: int) -> Optional[StoredPaths]: ...

    def ids_stored_since(self, instant: datetime) -> Set[int]: ...

    def remove_incomplete_writes(self) -> int:
        """Removes what an interrupted run left behind (SPEC §6) and returns how many
        files were removed."""
        ...
