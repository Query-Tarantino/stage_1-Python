from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class BookMetadata:
    book_id: int
    title: Optional[str]
    author: Optional[str]
    language: Optional[str]
    path: Path
