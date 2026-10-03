from __future__ import annotations

from pathlib import Path
from typing import Set

from tarantino_indexer.ports.sources.stopwords_loader import StopwordsLoader


class FileStopwordsLoader(StopwordsLoader):
    def __init__(self, file: Path):
        self.file = file

    def stopwords(self) -> Set[str]:
        if not self.file.exists():
            return set()
        return {
            line.strip().lower()
            for line in self.file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
