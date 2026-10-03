from __future__ import annotations

from pathlib import Path
from typing import List, Set

from tarantino_indexer.model.whitespace import JAVA_WHITESPACE
from tarantino_indexer.ports.sources.stopwords_loader import StopwordsLoader


class FileStopwordsLoader(StopwordsLoader):
    def __init__(self, file: Path):
        self.file = file

    def stopwords(self) -> Set[str]:
        entries = (line.strip(JAVA_WHITESPACE).lower() for line in self._lines())
        return {entry for entry in entries if entry}

    def _lines(self) -> List[str]:
        # Only \n ends a line (SPEC §1)
        return self.file.read_text(encoding="utf-8", newline="").split("\n")
