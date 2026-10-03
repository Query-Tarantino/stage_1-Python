from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BookMetadata:
    book_id: int
    title: str
    author: str
    language: str
    path: Path
