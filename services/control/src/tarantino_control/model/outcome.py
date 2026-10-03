from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Outcome:
    succeeded: bool
    detail: str

    @staticmethod
    def success(detail: str) -> Outcome:
        return Outcome(True, detail)

    @staticmethod
    def failure(detail: str) -> Outcome:
        return Outcome(False, detail)
