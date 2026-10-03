import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

import pytest

from tarantino_query.adapters.index.folders.term_files import TermFiles
from tarantino_query.commands.search_command import SearchCommand
from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.model.query_terms import QueryTerms
from tarantino_query.ports.inverted_index_reader import InvertedIndexReader
from tarantino_query.ports.metadata_reader import MetadataReader

# The cases of TARANTINO_WORKLOAD/conformance (SPEC §13); without the variable,
# those of this repository
WORKLOAD = Path(
    os.environ.get("TARANTINO_WORKLOAD") or Path(__file__).parents[4] / "workload"
)


def conformance(name: str) -> dict:
    return json.loads((WORKLOAD / "conformance" / name).read_text(encoding="utf-8"))


QUERY_TERMS = conformance("query_terms.json")
SEARCH = conformance("search.json")
FOLDERS_NAMES = conformance("folders_names.json")["cases"]


class InMemoryIndex(InvertedIndexReader):
    def __init__(self, postings: Dict[str, Set[int]]):
        self._postings = postings

    def postings(self, term: str) -> Set[int]:
        return self._postings.get(term, set())


class EveryBook(MetadataReader):
    def book(self, book_id: int) -> Optional[BookMetadata]:
        return BookMetadata(book_id, None, None, None, Path(f"{book_id}.body.txt"))

    def books_by(self, author: str) -> List[BookMetadata]:
        return []


@pytest.mark.parametrize(
    "case", QUERY_TERMS["cases"], ids=[case["name"] for case in QUERY_TERMS["cases"]]
)
def test_turns_queries_into_terms(case):
    assert QueryTerms.of(case["query"], set(QUERY_TERMS["stopwords"])) == case["terms"]


@pytest.mark.parametrize(
    "case", SEARCH["cases"], ids=[case["query"] for case in SEARCH["cases"]]
)
def test_finds_the_books_containing_every_term(case):
    stopwords = set(SEARCH["stopwords"])
    postings: Dict[str, Set[int]] = {}
    for book_id, text in SEARCH["books"].items():
        for term in QueryTerms.of(text, stopwords):
            postings.setdefault(term, set()).add(int(book_id))
    search = SearchCommand(InMemoryIndex(postings), EveryBook(), stopwords)

    assert [book.book_id for book in search.execute(case["query"]).books] == case["ids"]


@pytest.mark.parametrize(
    "case", FOLDERS_NAMES, ids=[case["name"] for case in FOLDERS_NAMES]
)
def test_names_term_files(case):
    root = Path("index")

    assert TermFiles.file(root, case["term"]) == root / case["path"]
