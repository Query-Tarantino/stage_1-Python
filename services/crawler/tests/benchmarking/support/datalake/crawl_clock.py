from __future__ import annotations

from datetime import datetime, timedelta


class CrawlClock:
    # The clock of a crawl that downloads 100 books per hour: the book at position i
    # is saved at start + ⌊i / 100⌋ hours (SPEC §11). Called, it gives the instant of
    # the book at its current position, as the clock of the time layout.
    BOOKS_PER_HOUR = 100

    def __init__(self, start: datetime):
        self._start = start
        self._position = 0

    @staticmethod
    def instant_of(start: datetime, position: int) -> datetime:
        return start + timedelta(hours=position // CrawlClock.BOOKS_PER_HOUR)

    @staticmethod
    def duration_of(books: int) -> timedelta:
        return timedelta(hours=-(-books // CrawlClock.BOOKS_PER_HOUR))

    def move_to(self, position: int) -> None:
        self._position = position

    def __call__(self) -> datetime:
        return self.instant_of(self._start, self._position)
