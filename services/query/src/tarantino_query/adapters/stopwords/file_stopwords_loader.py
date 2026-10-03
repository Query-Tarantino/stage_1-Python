from pathlib import Path
from typing import List, Set

from tarantino_query.ports.stopwords_loader import StopwordsLoader


class FileStopwordsLoader(StopwordsLoader):
    def __init__(self, file: Path):
        self.file = file

    def stopwords(self) -> Set[str]:
        if not self.file.exists():
            return set()
        return {line.strip().lower() for line in self._lines() if line.strip()}

    def _lines(self) -> List[str]:
        with open(self.file, "r", encoding="utf-8") as f:
            return f.readlines()
