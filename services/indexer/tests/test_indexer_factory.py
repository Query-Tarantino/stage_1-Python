from pathlib import Path

import pytest

from tarantino_indexer.adapters.datalake.batch.batch_based_datalake_reader import (
    BatchBasedDatalakeReader,
)
from tarantino_indexer.adapters.datalake.book.book_based_datalake_reader import (
    BookBasedDatalakeReader,
)
from tarantino_indexer.adapters.datalake.time.time_based_datalake_reader import (
    TimeBasedDatalakeReader,
)
from tarantino_indexer.adapters.index.folders.folder_per_term_index_adapter import (
    FolderPerTermIndexAdapter,
)
from tarantino_indexer.adapters.index.json.monolithic_json_index_adapter import (
    MonolithicJsonIndexAdapter,
)
from tarantino_indexer.adapters.metadata.sqlite_metadata_adapter import (
    SqliteMetadataAdapter,
)
from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.indexer_factory import IndexerFactory


def config(
    workload: Path, layout: str = "time", index: str = "json", metadata: str = "sqlite"
) -> IndexerConfig:
    return IndexerConfig(
        datalake=workload / "datalake",
        datalake_layout=layout,
        datamarts=workload / "datamarts",
        index=index,
        metadata=metadata,
        mongo_uri="mongodb://localhost:27017",
        workload=workload,
    )


def test_selects_the_configured_structures(tmp_path):
    readers = {
        "time": TimeBasedDatalakeReader,
        "book": BookBasedDatalakeReader,
        "batch": BatchBasedDatalakeReader,
    }
    for layout, reader in readers.items():
        assert isinstance(
            IndexerFactory.datalake_reader(config(tmp_path, layout=layout)), reader
        )
    assert isinstance(
        IndexerFactory.inverted_index(config(tmp_path, index="json")),
        MonolithicJsonIndexAdapter,
    )
    assert isinstance(
        IndexerFactory.inverted_index(config(tmp_path, index="folders")),
        FolderPerTermIndexAdapter,
    )
    assert isinstance(
        IndexerFactory.metadata(config(tmp_path, metadata="sqlite")),
        SqliteMetadataAdapter,
    )


def test_rejects_unknown_options(tmp_path):
    with pytest.raises(ValueError, match="^Unknown datalake layout: hash$"):
        IndexerFactory.datalake_reader(config(tmp_path, layout="hash"))
    with pytest.raises(ValueError, match="^Unknown index structure: trie$"):
        IndexerFactory.inverted_index(config(tmp_path, index="trie"))
    with pytest.raises(ValueError, match="^Unknown metadata backend: postgres$"):
        IndexerFactory.metadata(config(tmp_path, metadata="postgres"))


def test_tokenizer_removes_the_stopwords_of_the_workload(tmp_path):
    (tmp_path / "stopwords.txt").write_text("the\nof\n", encoding="utf-8")

    tokenizer = IndexerFactory.tokenizer(config(tmp_path))
    term_occurrences = tokenizer.occurrences(1, "The whale of the sea")

    assert term_occurrences.frequencies == {"whale": 1, "sea": 1}
