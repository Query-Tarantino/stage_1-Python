from __future__ import annotations

from typing import List, Protocol


class ControlStateStore(Protocol):
    # The ids of each control file, in file order and each one once (SPEC §9)
    def downloaded(self) -> List[int]: ...

    def indexed(self) -> List[int]: ...

    def mark_downloaded(self, book_id: int) -> None: ...

    def mark_indexed(self, book_id: int) -> None: ...
