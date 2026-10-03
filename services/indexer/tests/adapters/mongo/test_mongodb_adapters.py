from pathlib import Path

from pymongo.collection import Collection

from tarantino_indexer.adapters.index.mongo.mongodb_index_adapter import (
    MongodbIndexAdapter,
)
from tarantino_indexer.adapters.metadata.mongodb_metadata_adapter import (
    MongodbMetadataAdapter,
)
from tarantino_indexer.adapters.mongo.mongo_databases import MongoDatabases
from tarantino_indexer.model.book.book import Book
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


def postings(uri: str, term: str) -> list:
    document = MongoDatabases.database(uri)["inverted_index"].find_one({"term": term})
    return sorted(document["postings"])


def has_unique_index(uri: str, collection: str, field: str) -> bool:
    indexes = MongoDatabases.database(uri)[collection].index_information().values()
    return any(
        index["key"] == [(field, 1)] and index.get("unique") for index in indexes
    )


def test_index_adds_unique_postings_per_term(mongo_uri):
    index = MongodbIndexAdapter(mongo_uri)
    index.add(TermOccurrences(1342, {"island": 2, "whale": 1}))
    index.add(TermOccurrences(5, {"island": 1}))
    index.flush()
    index.add(TermOccurrences(5, {"island": 1}))
    index.flush()

    assert postings(mongo_uri, "island") == [5, 1342]
    assert postings(mongo_uri, "whale") == [1342]


def test_index_stores_one_document_per_term_under_a_unique_index(mongo_uri):
    index = MongodbIndexAdapter(mongo_uri)
    index.add(TermOccurrences(5, {"island": 1}))
    index.flush()
    document = MongoDatabases.database(mongo_uri)["inverted_index"].find_one(
        {"term": "island"}, {"_id": False}
    )

    assert document == {"term": "island", "postings": [5]}
    assert has_unique_index(mongo_uri, "inverted_index", "term")


def test_index_flushes_every_term_in_one_unordered_bulk_write_in_term_order(
    mongo_uri, monkeypatch
):
    bulk_writes = []
    bulk_write = Collection.bulk_write

    def recording_bulk_write(collection, requests, *args, **kwargs):
        bulk_writes.append(([request._filter["term"] for request in requests], kwargs))
        return bulk_write(collection, requests, *args, **kwargs)

    monkeypatch.setattr(Collection, "bulk_write", recording_bulk_write)
    index = MongodbIndexAdapter(mongo_uri)
    index.add(TermOccurrences(5, {"whale": 1, "island": 1, "écume": 1, "ahab": 1}))
    index.flush()

    assert bulk_writes == [(["ahab", "island", "whale", "écume"], {"ordered": False})]


def test_index_flush_without_pending_terms_writes_nothing(mongo_uri):
    MongodbIndexAdapter(mongo_uri).flush()

    assert MongoDatabases.database(mongo_uri)["inverted_index"].count_documents({}) == 0


def test_metadata_is_replaced_by_book_id(mongo_uri):
    metadata = MongodbMetadataAdapter(mongo_uri)
    metadata.save(
        Book(5, "Old title", None, "English", Path("datalake", "5", "body.txt"))
    )
    metadata.save(
        Book(5, "Robinson Crusoe", None, "English", Path("datalake", "5", "body.txt"))
    )
    books = MongoDatabases.database(mongo_uri)["books"]

    assert books.count_documents({}) == 1
    assert books.find_one({"book_id": 5}, {"_id": False}) == {
        "book_id": 5,
        "title": "Robinson Crusoe",
        "author": None,
        "language": "English",
        "path": "datalake/5/body.txt",
    }
    assert has_unique_index(mongo_uri, "books", "book_id")
