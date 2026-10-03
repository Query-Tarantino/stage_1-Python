from pathlib import Path
from typing import Set

from tarantino_query.adapters.index.folders.term_files import TermFiles
from tarantino_query.ports.inverted_index_reader import InvertedIndexReader


class FolderPerTermIndexReader(InvertedIndexReader):
    def __init__(self, folder: Path):
        self.folder = folder

    def postings(self, term: str) -> Set[int]:
        if not term:
            return set()
        term_file = TermFiles.file(self.folder, term)

        if not term_file.exists():
            return set()

        result = set()
        with open(term_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    result.add(int(line))
        return result
