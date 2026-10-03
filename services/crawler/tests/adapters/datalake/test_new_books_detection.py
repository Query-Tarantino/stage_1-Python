import os
from datetime import datetime, timedelta

from tarantino_crawler.adapters.datalake.batch.batch_based_datalake_adapter import (
    BatchBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.datalake.book.book_based_datalake_adapter import (
    BookBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.datalake.time.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from tarantino_crawler.model.book.book_text import BookText

THRESHOLD = datetime.fromisoformat("2025-09-25T15:30:00Z")


def save_at(root, book_id: int, instant: str) -> None:
    saved_at = datetime.fromisoformat(instant)
    TimeBasedDatalakeAdapter(root, lambda: saved_at).save(BookText(book_id, "h", "b"))


def assert_only_recent_books_detected(datalake) -> None:
    old_body = datalake.save(BookText(1, "header", "body")).body
    datalake.save(BookText(1500, "header", "body"))
    old = THRESHOLD - timedelta(seconds=60)
    nanoseconds = int(old.timestamp()) * 1_000_000_000
    os.utime(old_body, ns=(nanoseconds, nanoseconds))

    assert datalake.ids_stored_since(THRESHOLD) == {1500}


def test_time_layout_selects_hour_directories_from_the_hour_of_the_instant(tmp_path):
    save_at(tmp_path, 1, "2025-09-25T14:59:00Z")
    save_at(tmp_path, 2, "2025-09-25T15:10:00Z")
    save_at(tmp_path, 3, "2025-09-26T09:00:00Z")

    assert TimeBasedDatalakeAdapter(tmp_path).ids_stored_since(THRESHOLD) == {2, 3}


def test_book_layout_selects_bodies_modified_since_the_instant(tmp_path):
    assert_only_recent_books_detected(BookBasedDatalakeAdapter(tmp_path))


def test_batch_layout_selects_bodies_modified_since_the_instant(tmp_path):
    assert_only_recent_books_detected(BatchBasedDatalakeAdapter(tmp_path))


def test_compares_modification_times_in_nanoseconds(tmp_path):
    datalake = BookBasedDatalakeAdapter(tmp_path)
    body = datalake.save(BookText(7, "header", "body")).body
    nanoseconds = int(THRESHOLD.timestamp()) * 1_000_000_000
    os.utime(body, ns=(nanoseconds - 1, nanoseconds - 1))

    assert datalake.ids_stored_since(THRESHOLD) == set()


def test_empty_datalakes_detect_nothing(tmp_path):
    missing = tmp_path / "missing"

    assert BookBasedDatalakeAdapter(missing).ids_stored_since(THRESHOLD) == set()
    assert TimeBasedDatalakeAdapter(missing).ids_stored_since(THRESHOLD) == set()
