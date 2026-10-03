from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BookText:
    book_id: int
    header: str
    body: str
    body_path: Path
