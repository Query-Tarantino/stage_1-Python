from pathlib import Path

import pytest

from tarantino_query.adapters.index.folders.folder_per_term_index_reader import (
    FolderPerTermIndexReader,
)
from tarantino_query.adapters.index.json.monolithic_json_index_reader import (
    MonolithicJsonIndexReader,
)
from tarantino_query.adapters.metadata.sqlite_metadata_reader import (
    SqliteMetadataReader,
)
from tarantino_query.query_config import QueryConfig
from tarantino_query.query_factory import QueryFactory


def config(root: Path, index: str = "json", metadata: str = "sqlite") -> QueryConfig:
    return QueryConfig(
        datamarts=root / "datamarts",
        index=index,
        metadata=metadata,
        mongo_uri="mongodb://localhost:27017",
        workload=root / "workload",
    )


def test_selects_the_configured_structures(tmp_path):
    assert isinstance(
        QueryFactory.inverted_index(config(tmp_path, index="json")),
        MonolithicJsonIndexReader,
    )
    assert isinstance(
        QueryFactory.inverted_index(config(tmp_path, index="folders")),
        FolderPerTermIndexReader,
    )
    assert isinstance(
        QueryFactory.metadata(config(tmp_path, metadata="sqlite")),
        SqliteMetadataReader,
    )


def test_rejects_unknown_options(tmp_path):
    with pytest.raises(ValueError, match="^Unknown index structure: trie$"):
        QueryFactory.inverted_index(config(tmp_path, index="trie"))
    with pytest.raises(ValueError, match="^Unknown metadata backend: postgres$"):
        QueryFactory.metadata(config(tmp_path, metadata="postgres"))


def test_search_command_uses_the_stopwords_of_the_workload(tmp_path):
    (tmp_path / "workload").mkdir()
    (tmp_path / "workload" / "stopwords.txt").write_text("the\nof\n", encoding="utf-8")

    search = QueryFactory.search_command(config(tmp_path))

    assert search.stopwords == {"the", "of"}
