import json
import os
from pathlib import Path

import pytest

from tarantino_indexer.adapters.index.folders.term_files import TermFiles
from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.indexer_factory import IndexerFactory
from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.model.book.header_parser import HeaderParser
from tarantino_indexer.model.terms.tokenizer import Tokenizer

WORKLOAD = Path(
    os.environ.get("TARANTINO_WORKLOAD") or Path(__file__).parents[4] / "workload"
)


def conformance(name: str) -> dict:
    return json.loads((WORKLOAD / "conformance" / name).read_text(encoding="utf-8"))


DATALAKE_PATHS = conformance("datalake_paths.json")["cases"]
HEADER_FIELDS = conformance("header_fields.json")["cases"]
TERMS = conformance("terms.json")
FOLDERS_NAMES = conformance("folders_names.json")["cases"]


@pytest.mark.parametrize(
    "case",
    DATALAKE_PATHS,
    ids=[
        f"{case['layout']} {case['id']} at {case['saved_at']}"
        for case in DATALAKE_PATHS
    ],
)
def test_reads_books_at_their_layout_paths(case, tmp_path):
    book_id = case["id"]
    store(tmp_path / case["header"], f"header of {book_id}")
    body = store(tmp_path / case["body"], f"body of {book_id}")

    reader = IndexerFactory.datalake_reader(config(tmp_path, case["layout"]))

    assert reader.book_text(book_id) == BookText(
        book_id, f"header of {book_id}", f"body of {book_id}", body
    )


@pytest.mark.parametrize(
    "case", HEADER_FIELDS, ids=[case["name"] for case in HEADER_FIELDS]
)
def test_extracts_header_fields(case):
    book = HeaderParser().book(BookText(1, case["header"], "", Path("1.body.txt")))

    assert book.title == case["title"]
    assert book.author == case["author"]
    assert book.language == case["language"]


@pytest.mark.parametrize(
    "case", TERMS["cases"], ids=[case["name"] for case in TERMS["cases"]]
)
def test_counts_terms_of_a_body(case):
    tokenizer = Tokenizer(set(TERMS["stopwords"]))

    assert tokenizer.occurrences(1, case["text"]).frequencies == case["terms"]


@pytest.mark.parametrize(
    "case", FOLDERS_NAMES, ids=[case["name"] for case in FOLDERS_NAMES]
)
def test_names_term_files(case):
    root = Path("index")

    assert TermFiles.file(root, case["term"]) == root / case["path"]


def store(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")
    return file


def config(datalake: Path, layout: str) -> IndexerConfig:
    return IndexerConfig(
        datalake=datalake,
        datalake_layout=layout,
        datamarts=Path("datamarts"),
        index="json",
        metadata="sqlite",
        mongo_uri="mongodb://localhost:27017",
        workload=Path("workload"),
    )
