from pathlib import Path
from typing import Optional

import pytest

from tarantino_query.adapters.index.mongo.mongodb_index_reader import MongodbIndexReader
from tarantino_query.adapters.metadata.mongodb_metadata_reader import (
    MongodbMetadataReader,
)
from tarantino_query.adapters.mongo.mongo_databases import MongoDatabases
from tarantino_query.model.book_metadata import BookMetadata


def book(book_id: int, title: str, author: Optional[str]) -> dict:
    return {
        "book_id": book_id,
        "title": title,
        "author": author,
        "language": "English",
        "path": f"datalake/{book_id}/body.txt",
    }


@pytest.fixture
def stored(mongo_uri) -> str:
    database = MongoDatabases.database(mongo_uri)
    database["inverted_index"].insert_one({"term": "island", "postings": [1342, 5]})
    database["books"].insert_many(
        [
            book(76, "Huckleberry Finn", "Mark Twain"),
            book(74, "Tom Sawyer", "Mark Twain"),
            book(84, "Frankenstein", None),
        ]
    )
    return mongo_uri


def ids(books: list) -> list:
    return [found.book_id for found in books]


def test_reads_the_postings_of_a_term_and_nothing_for_unknown_terms(stored):
    index = MongodbIndexReader(stored)

    assert index.postings("island") == {5, 1342}
    assert index.postings("whale") == set()


def test_finds_a_book_by_id_keeping_missing_fields_as_null(stored):
    assert MongodbMetadataReader(stored).book(84) == BookMetadata(
        84, "Frankenstein", None, "English", Path("datalake/84/body.txt")
    )
    assert MongodbMetadataReader(stored).book(1) is None


def test_finds_books_by_case_insensitive_author_substring_ordered_by_id(stored):
    assert ids(MongodbMetadataReader(stored).books_by("twain")) == [74, 76]


def test_matches_regular_expression_metacharacters_in_authors_literally(mongo_uri):
    MongoDatabases.database(mongo_uri)["books"].insert_many(
        [book(1, "One", "J. R. R. (Tolkien)"), book(2, "Two", "JxRxRx Tolkien")]
    )

    assert ids(MongodbMetadataReader(mongo_uri).books_by("j. r. r. (")) == [1]
