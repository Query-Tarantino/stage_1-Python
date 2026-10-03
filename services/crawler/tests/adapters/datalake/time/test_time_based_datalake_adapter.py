from datetime import datetime, timedelta, timezone

import pytest

from tarantino_crawler.adapters.datalake.time.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from tarantino_crawler.model.book.book_text import BookText


@pytest.fixture
def clock():
    return lambda: datetime(2025, 9, 25, 14, 30, 0, tzinfo=timezone.utc)


def test_stores_books_under_day_and_hour_directories(tmp_path, clock):
    datalake = TimeBasedDatalakeAdapter(tmp_path, clock)
    paths = datalake.save(BookText(5, "header", "body"))

    expected_header = tmp_path / "20250925" / "14" / "5.header.txt"
    expected_body = tmp_path / "20250925" / "14" / "5.body.txt"

    assert expected_header == paths.header
    assert expected_body == paths.body

    assert expected_header.read_text(encoding="utf-8") == "header"
    assert expected_body.read_text(encoding="utf-8") == "body"


def test_finds_paths_of_stored_books_only(tmp_path, clock):
    datalake = TimeBasedDatalakeAdapter(tmp_path, clock)
    stored = datalake.save(BookText(5, "header", "body"))

    assert datalake.paths_of(5) == stored
    assert datalake.paths_of(6) is None


def test_finds_books_saved_in_earlier_hours(tmp_path, clock):
    earlier = TimeBasedDatalakeAdapter(tmp_path, clock).save(
        BookText(5, "header", "body")
    )

    def a_day_later():
        return clock() + timedelta(days=1)

    assert TimeBasedDatalakeAdapter(tmp_path, a_day_later).paths_of(5) == earlier


def test_looks_books_up_no_deeper_than_the_hour_directories(tmp_path, clock):
    too_deep = tmp_path / "20250925" / "14" / "extra"
    too_deep.mkdir(parents=True)
    (too_deep / "5.body.txt").write_text("body", encoding="utf-8")

    assert TimeBasedDatalakeAdapter(tmp_path, clock).paths_of(5) is None


def test_finds_no_book_without_a_datalake(tmp_path, clock):
    assert TimeBasedDatalakeAdapter(tmp_path / "missing", clock).paths_of(5) is None


def test_leaves_no_temporary_files_behind(tmp_path, clock):
    TimeBasedDatalakeAdapter(tmp_path, clock).save(BookText(5, "header", "body"))

    assert list(tmp_path.rglob("*.tmp")) == []
