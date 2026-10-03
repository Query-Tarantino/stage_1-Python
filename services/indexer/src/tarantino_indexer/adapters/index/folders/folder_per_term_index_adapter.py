from __future__ import annotations

import os
from pathlib import Path
from typing import Set

from tarantino_indexer.adapters.index.folders.term_files import TermFiles
from tarantino_indexer.adapters.index.pending_postings import PendingPostings
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)


class FolderPerTermIndexAdapter(InvertedIndexStorage):
    def __init__(self, directory: Path):
        self.directory = directory
        self._pending = PendingPostings()

    def add(self, occurrences: TermOccurrences) -> None:
        self._pending.add(occurrences)

    def flush(self) -> None:
        # Terms come in order, so the files of each folder are written together;
        # each folder is created once, and only the files that gain an id are
        # rewritten (SPEC §8.1)
        folders: Set[Path] = set()
        for term, ids in self._pending.drain():
            self._merge(TermFiles.file(self.directory, term), ids, folders)

    @classmethod
    def _merge(cls, file: Path, ids: Set[int], folders: Set[Path]) -> None:
        postings = cls._stored_postings(file)
        stored = len(postings)
        postings |= ids
        if len(postings) > stored:
            if file.parent not in folders:
                folders.add(file.parent)
                file.parent.mkdir(parents=True, exist_ok=True)
            cls._write_atomically(file, postings)

    @staticmethod
    def _stored_postings(file: Path) -> Set[int]:
        if not file.exists():
            return set()
        return {int(line) for line in file.read_text(encoding="utf-8").split()}

    @staticmethod
    def _write_atomically(file: Path, postings: Set[int]) -> None:
        temporary = file.with_name(file.name + ".tmp")
        content = "".join(f"{book_id}\n" for book_id in sorted(postings))
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, file)
