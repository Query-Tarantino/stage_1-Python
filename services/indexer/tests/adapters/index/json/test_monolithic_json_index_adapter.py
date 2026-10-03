import json

import pytest

from tarantino_indexer.adapters.index.json.monolithic_json_index_adapter import (
    MonolithicJsonIndexAdapter,
)
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


def test_writes_sorted_terms_with_sorted_unique_postings(tmp_path):
    file = tmp_path / "datamarts" / "inverted_index.json"
    index = MonolithicJsonIndexAdapter(file)
    index.add(TermOccurrences(1342, {"whale": 1, "island": 2}))
    index.add(TermOccurrences(5, {"island": 1}))
    index.add(TermOccurrences(5, {"island": 1}))
    index.flush()

    assert file.read_text(encoding="utf-8") == '{"island":[5,1342],"whale":[1342]}'


def test_writes_terms_in_utf8_as_they_are(tmp_path):
    file = tmp_path / "inverted_index.json"
    index = MonolithicJsonIndexAdapter(file)
    index.add(TermOccurrences(1342, {"écume": 1}))
    index.flush()

    assert file.read_bytes() == '{"écume":[1342]}'.encode("utf-8")


def test_merges_new_books_into_an_existing_index_file(tmp_path):
    file = tmp_path / "inverted_index.json"
    file.write_text('{"island":[5]}', encoding="utf-8")
    index = MonolithicJsonIndexAdapter(file)
    index.add(TermOccurrences(1342, {"island": 1}))
    index.flush()

    assert file.read_text(encoding="utf-8") == '{"island":[5,1342]}'


def test_opens_the_stored_index_into_memory_before_adding_books(tmp_path):
    file = tmp_path / "inverted_index.json"
    file.write_text('{"island":[5]}', encoding="utf-8")
    index = MonolithicJsonIndexAdapter(file)
    index.open()
    file.unlink()
    index.add(TermOccurrences(1342, {"whale": 1}))
    index.flush()

    assert file.read_text(encoding="utf-8") == '{"island":[5],"whale":[1342]}'


def test_fails_on_a_damaged_index_file_instead_of_replacing_it(tmp_path):
    file = tmp_path / "inverted_index.json"
    file.write_text('{"island":[5', encoding="utf-8")
    index = MonolithicJsonIndexAdapter(file)

    with pytest.raises(json.JSONDecodeError):
        index.add(TermOccurrences(1342, {"whale": 1}))
    assert file.read_text(encoding="utf-8") == '{"island":[5'
