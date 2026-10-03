from pathlib import Path

from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.indexer_factory import IndexerFactory


def config(workload: Path) -> IndexerConfig:
    return IndexerConfig(
        datalake=workload / "datalake",
        datalake_layout="time",
        datamarts=workload / "datamarts",
        index="json",
        metadata="sqlite",
        mongo_uri="mongodb://localhost:27017",
        workload=workload,
    )


def test_tokenizer_removes_the_stopwords_of_the_workload(tmp_path):
    (tmp_path / "stopwords.txt").write_text("the\nof\n", encoding="utf-8")

    tokenizer = IndexerFactory.tokenizer(config(tmp_path))
    term_occurrences = tokenizer.occurrences(1, "The whale of the sea")

    assert term_occurrences.frequencies == {"whale": 1, "sea": 1}
