import pytest

from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.crawler_factory import CrawlerFactory
from tarantino_crawler.model.book.book_text import BookText


def remaining_files(root) -> set:
    return {file for file in root.rglob("*") if file.is_file()}


@pytest.mark.parametrize("layout", ["time", "book", "batch"])
def test_removes_temporary_files_and_headers_without_body_but_keeps_stored_books(
    layout, tmp_path
):
    datalake = CrawlerFactory.datalake(CrawlerConfig(tmp_path, layout))
    stored = datalake.save(BookText(1342, "header", "body"))
    interrupted = datalake.save(BookText(2001, "header", "body"))
    interrupted.body.rename(interrupted.body.with_name(interrupted.body.name + ".tmp"))

    assert datalake.remove_incomplete_writes() == 2
    assert remaining_files(tmp_path) == {stored.header, stored.body}
    assert datalake.paths_of(1342) == stored


@pytest.mark.parametrize("layout", ["time", "book", "batch"])
def test_removes_nothing_from_an_empty_or_missing_datalake(layout, tmp_path):
    datalake = CrawlerFactory.datalake(CrawlerConfig(tmp_path / "missing", layout))

    assert datalake.remove_incomplete_writes() == 0


def test_removes_the_directories_left_empty(tmp_path):
    datalake = CrawlerFactory.datalake(CrawlerConfig(tmp_path, "book"))
    interrupted = datalake.save(BookText(2001, "header", "body"))
    interrupted.body.unlink()

    datalake.remove_incomplete_writes()

    assert list(tmp_path.iterdir()) == []
