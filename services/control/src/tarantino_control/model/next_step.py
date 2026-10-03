from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple


class Action(Enum):
    INDEX = auto()
    DOWNLOAD = auto()
    IDLE = auto()


@dataclass(frozen=True)
class NextStep:
    action: Action
    book_ids: Tuple[int, ...]

    @staticmethod
    def index(book_ids: List[int]) -> NextStep:
        return NextStep(Action.INDEX, tuple(book_ids))

    @staticmethod
    def download(book_id: int) -> NextStep:
        return NextStep(Action.DOWNLOAD, (book_id,))

    @staticmethod
    def idle() -> NextStep:
        return NextStep(Action.IDLE, ())

    def books(self) -> str:
        # The book id, or "<n> books (<first>…<last>)" for a batch of more (SPEC §15)
        if not self.book_ids:
            return ""
        if len(self.book_ids) == 1:
            return str(self.book_ids[0])
        return f"{len(self.book_ids)} books ({self.book_ids[0]}…{self.book_ids[-1]})"
