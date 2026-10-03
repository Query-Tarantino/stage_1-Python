from datetime import datetime, timedelta

from tarantino_crawler.adapters.datalake.time.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from tarantino_crawler.model.book.book_text import BookText

from services.crawler.tests.benchmarking.support.datalake.crawl_clock import CrawlClock
from services.crawler.tests.benchmarking.support.files.directories import Directories

START = datetime.fromisoformat("2025-09-25T23:00:00Z")


def test_advances_one_hour_every_hundred_books():
    assert CrawlClock.instant_of(START, 99) == START
    assert CrawlClock.instant_of(START, 100) == START + timedelta(hours=1)
    assert CrawlClock.duration_of(250) == timedelta(hours=3)


def test_spreads_the_time_layout_over_one_hour_directory_per_hundred_books(tmp_path):
    clock = CrawlClock(START)
    datalake = TimeBasedDatalakeAdapter(tmp_path, clock)
    for position in range(250):
        clock.move_to(position)
        datalake.save(BookText(position + 1, "header", "body"))

    assert Directories.footprint(tmp_path).directories == 5
