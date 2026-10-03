from pathlib import Path
from typing import Optional

from tarantino_control.control_config import ControlConfig
from tarantino_control.control_factory import ControlFactory
from tarantino_crawler.crawler_config import CrawlerConfig


def write(root: Path, file: str, content: bytes) -> None:
    (root / file).parent.mkdir(parents=True, exist_ok=True)
    (root / file).write_bytes(content)


def config(root: Path) -> ControlConfig:
    return ControlConfig(root / "control", root / "workload", 8, 100)


def crawler(root: Path, mirror: Optional[Path]) -> CrawlerConfig:
    return CrawlerConfig(root / "datalake", "time", mirror)


def test_takes_the_candidates_of_the_workload_file_given_even_with_a_mirror(tmp_path):
    write(tmp_path, "workload/book_ids.txt", b"84\n\n 1342 \r\n")
    write(tmp_path, "mirror/11/pg11.txt", b"text")

    candidates = ControlFactory.candidates(
        config(tmp_path), crawler(tmp_path, tmp_path / "mirror"), "book_ids.txt"
    )

    assert candidates == [84, 1342]


def test_takes_every_book_of_the_mirror_in_id_order_without_a_file(tmp_path):
    write(tmp_path, "mirror/1342/pg1342.txt", b"text")
    write(tmp_path, "mirror/84/pg84.txt", b"text")

    candidates = ControlFactory.candidates(
        config(tmp_path), crawler(tmp_path, tmp_path / "mirror"), None
    )

    assert candidates == [84, 1342]


def test_takes_the_sample_without_a_file_or_a_mirror(tmp_path):
    write(tmp_path, "workload/sample_ids.txt", b"1342\n84\n")

    assert ControlFactory.candidates(
        config(tmp_path), crawler(tmp_path, None), None
    ) == [
        1342,
        84,
    ]
