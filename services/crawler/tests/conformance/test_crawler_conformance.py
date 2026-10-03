import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from tarantino_crawler.adapters.datalake.time.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.crawler_factory import CrawlerFactory
from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.gutenberg_text import GutenbergText
from tarantino_crawler.model.failure.download_exception import DownloadException

# The cases of TARANTINO_WORKLOAD/conformance (SPEC §13); without the variable,
# those of this repository
WORKLOAD = Path(
    os.environ.get("TARANTINO_WORKLOAD") or Path(__file__).parents[4] / "workload"
)


def conformance(name: str) -> dict:
    return json.loads((WORKLOAD / "conformance" / name).read_text(encoding="utf-8"))


SPLIT = conformance("split.json")["cases"]
DATALAKE_PATHS = conformance("datalake_paths.json")["cases"]


@pytest.mark.parametrize("case", SPLIT, ids=[case["name"] for case in SPLIT])
def test_splits_header_and_body(case):
    if "failure" in case:
        with pytest.raises(DownloadException) as failure:
            GutenbergText.book_text(1, case["raw"])
        assert failure.value.reason.name == case["failure"]
    else:
        text = GutenbergText.book_text(1, case["raw"])
        assert text.header == case["header"]
        assert text.body == case["body"]


@pytest.mark.parametrize(
    "case",
    DATALAKE_PATHS,
    ids=[
        f"{case['layout']} {case['id']} at {case['saved_at']}"
        for case in DATALAKE_PATHS
    ],
)
def test_stores_books_at_their_layout_paths(case, tmp_path):
    paths = datalake(case, tmp_path).save(BookText(case["id"], "header", "body"))

    assert paths.header.relative_to(tmp_path).as_posix() == case["header"]
    assert paths.body.relative_to(tmp_path).as_posix() == case["body"]


def datalake(case: dict, root: Path):
    if case["layout"] != "time":
        return CrawlerFactory.datalake(CrawlerConfig(root, case["layout"]))
    saved_at = datetime.fromisoformat(case["saved_at"])
    return TimeBasedDatalakeAdapter(root, lambda: saved_at)
