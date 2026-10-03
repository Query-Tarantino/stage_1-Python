from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Action(Enum):
    INDEX = auto()
    DOWNLOAD = auto()
    IDLE = auto()


@dataclass(frozen=True)
class NextStep:
    action: Action
    book_id: int

    @staticmethod
    def index(book_id: int) -> NextStep:
        return NextStep(Action.INDEX, book_id)

    @staticmethod
    def download(book_id: int) -> NextStep:
        return NextStep(Action.DOWNLOAD, book_id)

    @staticmethod
    def idle() -> NextStep:
        return NextStep(Action.IDLE, 0)
