import pytest

from tarantino_control.control_config import ControlConfig


def test_reads_positive_integers():
    assert ControlConfig.positive_integer("TARANTINO_INDEX_BATCH", "100") == 100
    assert ControlConfig.positive_integer("TARANTINO_PARALLEL_DOWNLOADS", " 1 ") == 1


def test_rejects_values_that_are_not_positive_integers_naming_the_variable():
    with pytest.raises(ValueError) as error:
        ControlConfig.positive_integer("TARANTINO_PARALLEL_DOWNLOADS", "0")
    assert str(error.value) == (
        "Unknown TARANTINO_PARALLEL_DOWNLOADS: 0 (expected a positive integer)"
    )

    with pytest.raises(ValueError):
        ControlConfig.positive_integer("TARANTINO_INDEX_BATCH", "many")


def test_downloads_8_books_at_once_and_indexes_batches_of_100_by_default(monkeypatch):
    monkeypatch.delenv("TARANTINO_PARALLEL_DOWNLOADS", raising=False)
    monkeypatch.delenv("TARANTINO_INDEX_BATCH", raising=False)
    config = ControlConfig.from_environment()

    assert (config.parallel_downloads, config.index_batch) == (8, 100)
