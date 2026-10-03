from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class TermOccurrences:
    book_id: int
    frequencies: Dict[str, int]
