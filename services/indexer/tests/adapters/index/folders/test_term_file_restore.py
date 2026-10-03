from pathlib import Path
from typing import Dict

from tarantino_indexer.adapters.index.folders.folder_per_term_index_adapter import (
    FolderPerTermIndexAdapter,
)
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences

from services.indexer.tests.adapters.index.folders.term_file_restore import (
    TermFileRestore,
)


def index_book(root: Path, book_id: int, *terms: str) -> None:
    index = FolderPerTermIndexAdapter(root)
    index.add(TermOccurrences(book_id, {term: 1 for term in terms}))
    index.flush()


def files(root: Path) -> Dict[Path, str]:
    return {
        file.relative_to(root): file.read_text(encoding="utf-8")
        for file in root.rglob("*")
        if file.is_file()
    }


def test_undoes_an_update_by_restoring_only_the_touched_terms(tmp_path):
    snapshot, index = tmp_path / "snapshot", tmp_path / "index"
    index_book(snapshot, 1, "island", "whale")
    index_book(index, 1, "island", "whale")
    index_book(index, 2, "island", "écume")

    TermFileRestore.restore(snapshot, index, {"island", "écume"})

    assert files(index) == files(snapshot)
