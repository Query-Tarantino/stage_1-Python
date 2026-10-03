from pathlib import Path
from typing import List, Set

from tarantino_query.model.whitespace import JAVA_WHITESPACE
from tarantino_query.ports.stopwords_loader import StopwordsLoader


class FileStopwordsLoader(StopwordsLoader):
    def __init__(self, file: Path):
        self.file = file

    def stopwords(self) -> Set[str]:
        entries = (line.strip(JAVA_WHITESPACE).lower() for line in self._lines())
        return {entry for entry in entries if entry}

    def _lines(self) -> List[str]:
        return self.file.read_text(encoding="utf-8", newline="").split("\n")
