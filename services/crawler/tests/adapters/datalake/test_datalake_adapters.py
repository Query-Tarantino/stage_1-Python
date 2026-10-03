import os
from datetime import datetime, timezone

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
from tarantino_crawler.model.book.book_text import BookText

LAYOUTS = {
    "time": lambda root: TimeBasedDatalakeAdapter(
        root, lambda: datetime(2025, 9, 25, 14, 30, tzinfo=timezone.utc)
    ),
    "book": BookBasedDatalakeAdapter,
    "batch": BatchBasedDatalakeAdapter,
}


@pytest.mark.parametrize("layout", LAYOUTS)
def test_an_interrupted_save_leaves_its_header_but_no_book(
    layout, tmp_path, monkeypatch
):
    datalake = LAYOUTS[layout](tmp_path)
    replace = os.replace

    def interrupted_before_the_body(source, target):
        if str(target).endswith("body.txt"):
            raise OSError("interrupted")
        replace(source, target)

    monkeypatch.setattr(os, "replace", interrupted_before_the_body)
    with pytest.raises(OSError):
        datalake.save(BookText(5, "header", "body"))
    monkeypatch.undo()

    assert len(list(tmp_path.rglob("*header.txt"))) == 1
    assert datalake.paths_of(5) is None


@pytest.mark.parametrize("layout", LAYOUTS)
def test_a_book_exists_if_and_only_if_its_body_file_does(layout, tmp_path):
    datalake = LAYOUTS[layout](tmp_path)
    paths = datalake.save(BookText(5, "header", "body"))

    paths.header.unlink()
    assert datalake.paths_of(5) == paths

    paths.body.unlink()
    assert datalake.paths_of(5) is None


@pytest.mark.parametrize("layout", LAYOUTS)
def test_writes_the_text_as_given_with_lf_line_endings(layout, tmp_path):
    paths = LAYOUTS[layout](tmp_path).save(
        BookText(5, "Title: A\nB", "line\nnext\rsame")
    )

    assert paths.header.read_bytes() == b"Title: A\nB"
    assert paths.body.read_bytes() == b"line\nnext\rsame"
