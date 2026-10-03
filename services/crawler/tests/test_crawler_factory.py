from pathlib import Path

import pytest

from tarantino_crawler.adapters.datalake.batch.batch_based_datalake_adapter import (
    BatchBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.datalake.book.book_based_datalake_adapter import (
    BookBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.datalake.time.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.gutenberg.gutenberg_http_downloader import (
    GutenbergHttpDownloader,
)
from tarantino_crawler.adapters.gutenberg.local_mirror_downloader import (
    LocalMirrorDownloader,
)
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.crawler_factory import CrawlerFactory


def config(layout: str) -> CrawlerConfig:
    return CrawlerConfig(Path("datalake"), layout)


def test_selects_the_configured_datalake_layout():
    assert isinstance(CrawlerFactory.datalake(config("time")), TimeBasedDatalakeAdapter)
    assert isinstance(CrawlerFactory.datalake(config("book")), BookBasedDatalakeAdapter)
    assert isinstance(
        CrawlerFactory.datalake(config("batch")), BatchBasedDatalakeAdapter
    )


def test_downloads_over_http_unless_a_local_mirror_is_configured():
    with_mirror = CrawlerConfig(Path("datalake"), "batch", Path("mirror"))

    assert isinstance(
        CrawlerFactory.downloader(config("batch")), GutenbergHttpDownloader
    )
    assert isinstance(CrawlerFactory.downloader(with_mirror), LocalMirrorDownloader)


def test_rejects_unknown_layouts():
    with pytest.raises(ValueError, match="hash"):
        CrawlerFactory.datalake(config("hash"))


def test_reads_the_local_mirror_of_the_environment(monkeypatch):
    monkeypatch.setenv("TARANTINO_MIRROR", "mirror")
    assert CrawlerConfig.from_environment().mirror == Path("mirror")

    monkeypatch.setenv("TARANTINO_MIRROR", " ")
    assert CrawlerConfig.from_environment().mirror is None
