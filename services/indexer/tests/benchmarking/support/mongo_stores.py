from __future__ import annotations

from typing import Collection

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.uri_parser import parse_uri


class MongoStores:
    DEFAULT_INDEX = "_id_"

    @staticmethod
    def drop(uri: str) -> None:
        with MongoClient(uri) as client:
            client.drop_database(MongoStores._name(uri))

    @staticmethod
    def copy(source_uri: str, target_uri: str) -> None:
        with MongoClient(source_uri) as client:
            source = client[MongoStores._name(source_uri)]
            target = client[MongoStores._name(target_uri)]
            for name in source.list_collection_names():
                source[name].aggregate([{"$out": {"db": target.name, "coll": name}}])
                for index in source[name].list_indexes():
                    if index["name"] != MongoStores.DEFAULT_INDEX:
                        target[name].create_index(
                            list(index["key"].items()),
                            name=index["name"],
                            unique=index.get("unique", False),
                        )

    @staticmethod
    def restore_documents(
        snapshot_uri: str,
        target_uri: str,
        collection: str,
        field: str,
        values: Collection[str],
    ) -> None:
        documents_of_values = {field: {"$in": list(values)}}
        with MongoClient(snapshot_uri) as client:
            target = client[MongoStores._name(target_uri)][collection]
            target.delete_many(documents_of_values)
            snapshot = client[MongoStores._name(snapshot_uri)][collection]
            stored = list(snapshot.find(documents_of_values))
            if stored:
                target.insert_many(stored, ordered=False)

    @staticmethod
    def document_count(uri: str, collection: str) -> int:
        with MongoClient(uri) as client:
            return client[MongoStores._name(uri)][collection].count_documents({})

    @staticmethod
    def disk_usage(uri: str) -> int:
        with MongoClient(uri) as client:
            client.admin.command("fsync")
            database = client[MongoStores._name(uri)]
            return sum(
                MongoStores._stored_bytes(database, name)
                for name in database.list_collection_names()
            )

    @staticmethod
    def _stored_bytes(database: Database, collection: str) -> int:
        statistics = next(
            database[collection].aggregate([{"$collStats": {"storageStats": {}}}])
        )["storageStats"]
        return statistics["storageSize"] + statistics["totalIndexSize"]

    @staticmethod
    def _name(uri: str) -> str:
        return parse_uri(uri)["database"]
