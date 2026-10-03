import unicodedata

import pytest

from tarantino_indexer.adapters.index.folders.folder_per_term_index_adapter import (
    FolderPerTermIndexAdapter,
)
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


def test_merges_sorted_unique_postings_into_one_file_per_term(tmp_path):
    index = FolderPerTermIndexAdapter(tmp_path)
    index.add(TermOccurrences(1342, {"island": 3, "écume": 1}))
    index.flush()
    index.add(TermOccurrences(5, {"island": 1}))
    index.add(TermOccurrences(1342, {"island": 3}))
    index.flush()

    assert (tmp_path / "i" / "island.txt").read_bytes() == b"5\n1342\n"
    assert (tmp_path / "%C3%A9" / "%C3%A9cume.txt").read_bytes() == b"1342\n"


def test_keeps_apart_terms_that_insensitive_file_systems_would_merge(tmp_path):
    terms = [
        "shape",
        "ſhape",
        "heißt",
        "heisst",
        "λόγος",
        "λόγοσ",
        unicodedata.normalize("NFC", "café"),
        unicodedata.normalize("NFD", "café"),
    ]
    index = FolderPerTermIndexAdapter(tmp_path)
    for book_id, term in enumerate(terms, start=1):
        index.add(TermOccurrences(book_id, {term: 1}))
    index.flush()

    assert len([file for file in tmp_path.rglob("*") if file.is_file()]) == len(terms)


def test_a_failed_flush_does_not_fail_the_next_one(tmp_path):
    (tmp_path / "a").write_text(
        "a file where the folder of the terms in a would go", encoding="utf-8"
    )
    index = FolderPerTermIndexAdapter(tmp_path)
    index.add(TermOccurrences(1, {"apple": 1}))
    with pytest.raises(OSError):
        index.flush()

    index.add(TermOccurrences(2, {"whale": 1}))
    index.flush()

    assert (tmp_path / "w" / "whale.txt").read_text(encoding="utf-8").split() == ["2"]
