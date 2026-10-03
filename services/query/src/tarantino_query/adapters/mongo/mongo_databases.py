from __future__ import annotations

import threading
from typing import Dict

from pymongo import MongoClient
from pymongo.database import Database


class MongoDatabases:
    # One client per connection string and process, opened the first time it is needed
    # and reused for every database and collection, with the driver's default pool,
    # timeouts and write concern (SPEC §8.1)
    DEFAULT_DATABASE = "tarantino"
    _clients: Dict[str, MongoClient] = {}
    _lock = threading.Lock()

    @staticmethod
    def database(uri: str) -> Database:
        with MongoDatabases._lock:
            client = MongoDatabases._clients.get(uri)
            if client is None:
                client = MongoDatabases._clients[uri] = MongoClient(uri)
        # The database named in the path of the connection string, or tarantino
        return client.get_default_database(MongoDatabases.DEFAULT_DATABASE)
