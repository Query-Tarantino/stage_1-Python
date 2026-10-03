from tarantino_query.adapters.mongo.mongo_databases import MongoDatabases


def test_uses_the_database_of_the_connection_string_or_tarantino():
    assert MongoDatabases.database("mongodb://localhost:27017").name == "tarantino"
    assert (
        MongoDatabases.database("mongodb://localhost:27017/tarantino_benchmark").name
        == "tarantino_benchmark"
    )


def test_opens_one_client_per_connection_string():
    uri = "mongodb://localhost:27017/tarantino_benchmark"

    assert MongoDatabases.database(uri).client is MongoDatabases.database(uri).client
