from pathlib import Path
from typing import List

import pytest

from tarantino_control.commands.control_pipeline import ControlPipeline
from tarantino_control.control_config import ControlConfig
from tarantino_control.control_factory import ControlFactory
from tarantino_control.model.next_step import Action
from tarantino_control.model.step_report import StepReport
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_query.commands.search_command import SearchCommand
from tarantino_query.query_config import QueryConfig
from tarantino_query.query_factory import QueryFactory

# The whole pipeline over a local mirror of three small books: with no candidates file
# the control service takes every book of the mirror, three at once, into the datalake
# and indexes them in batches, and the query service finds them by their words.
# Downloads finish in any order, so only the batches' sizes are fixed (SPEC §17).
PARALLEL_DOWNLOADS = 3
INDEX_BATCH = 2
UNUSED_MONGO = "mongodb://localhost:27017"


def gutenberg_text(title: str, author: str, language: str, body: str) -> str:
    # A book as Project Gutenberg publishes it: header, start marker, body, end marker
    # and footer, with CRLF
    marker = f" OF THE PROJECT GUTENBERG EBOOK {title.upper()} ***"
    return "\r\n".join(
        [
            f"The Project Gutenberg eBook of {title}",
            "",
            f"Title: {title}",
            "",
            f"Author: {author}",
            "",
            f"Language: {language}",
            "",
            f"*** START{marker}",
            "",
            body,
            "",
            f"*** END{marker}",
            "",
            "Updated editions will replace the previous one.",
            "",
        ]
    )


MIRROR_BOOKS = {
    11: gutenberg_text(
        "Alice's Adventures in Wonderland",
        "Lewis Carroll",
        "English",
        "Alice was beginning to get very tired of sitting by her sister on the bank,"
        " and of having nothing to do.",
    ),
    84: gutenberg_text(
        "Frankenstein; Or, The Modern Prometheus",
        "Mary Wollstonecraft Shelley",
        "English",
        "You will rejoice to hear that no disaster has accompanied the commencement of"
        " an enterprise which you have regarded with such evil forebodings. I arrived"
        " here yesterday, and my first task is to assure my dear sister of my welfare"
        " and increasing confidence in the success of my undertaking.",
    ),
    2000: gutenberg_text(
        "Don Quijote",
        "Miguel de Cervantes Saavedra",
        "Spanish",
        "En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho"
        " tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua,"
        " rocín flaco y galgo corredor.",
    ),
}


@pytest.mark.parametrize(
    "layout, index, metadata",
    [
        ("time", "json", "sqlite"),
        ("book", "folders", "sqlite"),
        ("batch", "mongo", "mongo"),
    ],
    ids=[
        "time datalake, json index, sqlite metadata",
        "book datalake, folders index, sqlite metadata",
        "batch datalake, mongo index, mongo metadata",
    ],
)
def test_downloads_indexes_and_finds_every_book_of_a_mirror(
    layout, index, metadata, tmp_path, request
):
    mongo_uri = (
        request.getfixturevalue("mongo_uri")
        if "mongo" in (index, metadata)
        else UNUSED_MONGO
    )
    workload = make_workload(tmp_path)
    control = ControlConfig(
        tmp_path / "control", workload, PARALLEL_DOWNLOADS, INDEX_BATCH
    )
    crawler = CrawlerConfig(tmp_path / "datalake", layout, make_mirror(tmp_path))
    pipeline = ControlFactory.pipeline(
        control,
        crawler,
        IndexerConfig(
            tmp_path / "datalake",
            layout,
            tmp_path / "datamarts",
            index,
            metadata,
            mongo_uri,
            workload,
        ),
        ControlFactory.candidates(control, crawler, None),
    )

    reports = run(pipeline)

    assert all(report.outcome.succeeded for report in reports), reports
    assert books(reports, Action.DOWNLOAD) == [11, 84, 2000]
    assert [
        len(report.step.book_ids)
        for report in reports
        if report.step.action == Action.INDEX
    ] == [2, 1]
    indexed = (tmp_path / "control" / "indexed_books.txt").read_text().splitlines()
    assert set(indexed) == {"11", "84", "2000"}
    search = QueryFactory.search_command(
        QueryConfig(tmp_path / "datamarts", index, metadata, mongo_uri, workload)
    )
    assert found(search, "sister") == [
        "11 Alice's Adventures in Wonderland by Lewis Carroll",
        "84 Frankenstein; Or, The Modern Prometheus by Mary Wollstonecraft Shelley",
    ]
    assert found(search, "tired sister") == [
        "11 Alice's Adventures in Wonderland by Lewis Carroll"
    ]
    assert found(search, "rocín") == [
        "2000 Don Quijote by Miguel de Cervantes Saavedra"
    ]
    assert found(search, "whale") == []


def make_mirror(root: Path) -> Path:
    mirror = root / "mirror"
    for book_id, text in MIRROR_BOOKS.items():
        file = mirror / str(book_id) / f"pg{book_id}.txt"
        file.parent.mkdir(parents=True)
        file.write_text(text, encoding="utf-8")
    return mirror


def make_workload(root: Path) -> Path:
    workload = root / "workload"
    workload.mkdir()
    (workload / "stopwords.txt").write_text("the\nof\nand\n", encoding="utf-8")
    return workload


def run(pipeline: ControlPipeline) -> List[StepReport]:
    reports = []
    report = pipeline.run_step()
    while not report.idle():
        reports.append(report)
        report = pipeline.run_step()
    return reports


def books(reports: List[StepReport], action: Action) -> List[int]:
    return sorted(
        book_id
        for report in reports
        if report.step.action == action
        for book_id in report.step.book_ids
    )


def found(search: SearchCommand, query: str) -> List[str]:
    return [
        f"{book.book_id} {book.title} by {book.author}"
        for book in search.execute(query).books
    ]
