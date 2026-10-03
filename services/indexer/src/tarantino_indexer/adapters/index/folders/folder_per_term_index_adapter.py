from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)


class FolderPerTermIndexAdapter(InvertedIndexStorage):
    def __init__(self, directory: Path):
        self.directory = directory
        self._memory: Dict[str, Set[int]] = defaultdict(set)

    def add(self, occurrences: TermOccurrences) -> None:
        for term in occurrences.frequencies.keys():
            self._memory[term].add(occurrences.book_id)

    def flush(self) -> None:
        # Taken out before writing, so a flush that fails does not leave its terms
        # behind to fail the next one too.
        pending, self._memory = self._memory, defaultdict(set)
        for term, new_ids in pending.items():
            if not term:
                continue
            first_char = term[0].lower()
            term_dir = self.directory / first_char
            term_dir.mkdir(parents=True, exist_ok=True)

            term_file = term_dir / f"{term}.txt"
            existing_ids = set()

            if term_file.exists():
                with open(term_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            existing_ids.add(int(line))

            all_ids = sorted(existing_ids.union(new_ids))

            tmp_file = term_dir / f"{term}.tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                for book_id in all_ids:
                    f.write(f"{book_id}\n")

            os.replace(tmp_file, term_file)
