from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Collection, Set

from tarantino_indexer.adapters.index.folders.term_files import TermFiles


class TermFileRestore:
    # Puts back the term files of some terms as they are in a snapshot, deleting the
    # ones it does not have. Files are restored in parallel, and each folder is created
    # before the first file copied into it.

    @staticmethod
    def restore(snapshot: Path, index: Path, terms: Collection[str]) -> None:
        folders: Set[Path] = set()
        with ThreadPoolExecutor() as pool:
            list(
                pool.map(
                    lambda term: TermFileRestore._restore(
                        TermFiles.file(snapshot, term),
                        TermFiles.file(index, term),
                        folders,
                    ),
                    terms,
                )
            )

    @staticmethod
    def _restore(stored: Path, current: Path, folders: Set[Path]) -> None:
        if not stored.exists():
            current.unlink(missing_ok=True)
            return
        if current.parent not in folders:
            current.parent.mkdir(parents=True, exist_ok=True)
            folders.add(current.parent)
        shutil.copyfile(stored, current)
