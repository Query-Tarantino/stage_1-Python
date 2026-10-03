import os
import uuid
from urllib.parse import urlsplit, urlunsplit

import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

SERVER = os.environ.get("TARANTINO_MONGO_URI", "mongodb://localhost:27017")


@pytest.fixture(scope="session")
def mongo_server() -> str:
    client = MongoClient(SERVER, serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except PyMongoError:
        pytest.skip(f"No MongoDB answers at {SERVER}")
    finally:
        client.close()
    return SERVER


@pytest.fixture
def mongo_uri(mongo_server: str):
    name = "tarantino_test_" + uuid.uuid4().hex
    yield urlunsplit(urlsplit(mongo_server)._replace(path="/" + name))
    with MongoClient(mongo_server) as client:
        client.drop_database(name)
