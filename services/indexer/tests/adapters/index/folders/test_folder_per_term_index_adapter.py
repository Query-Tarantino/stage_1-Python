import pytest

from tarantino_indexer.adapters.index.folders.folder_per_term_index_adapter import (
    FolderPerTermIndexAdapter,
)
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences

TERM_LONGER_THAN_A_FILE_NAME = "a" * 300


def test_a_failed_flush_does_not_fail_the_next_one(tmp_path):
    index = FolderPerTermIndexAdapter(tmp_path)
    index.add(TermOccurrences(1, {TERM_LONGER_THAN_A_FILE_NAME: 1}))
    with pytest.raises(OSError):
        index.flush()

    index.add(TermOccurrences(2, {"whale": 1}))
    index.flush()

    assert (tmp_path / "w" / "whale.txt").read_text(encoding="utf-8").split() == ["2"]
