import os

from services.crawler.tests.benchmarking.support.files.directories import Directories
from services.crawler.tests.benchmarking.support.files.footprint import Footprint


def test_measures_files_directories_and_bytes_rounded_up_to_whole_blocks(tmp_path):
    block = os.statvfs(tmp_path).f_frsize
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "empty.txt").write_bytes(b"")
    (tmp_path / "a" / "one.txt").write_bytes(b"x")
    (tmp_path / "a" / "b" / "block.txt").write_bytes(b"x" * block)
    (tmp_path / "a" / "b" / "more.txt").write_bytes(b"x" * (block + 1))

    assert Directories.footprint(tmp_path) == Footprint(4, 2, 2 * block + 2, 4 * block)


def test_measures_nothing_for_a_missing_directory(tmp_path):
    assert Directories.footprint(tmp_path / "missing") == Footprint.NONE


def test_copies_a_tree_and_deletes_it_with_its_root(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    (source / "a" / "b").mkdir(parents=True)
    (source / "a" / "b" / "term.txt").write_text("1\n2\n", encoding="utf-8")
    (source / "empty").mkdir()

    Directories.copy(source, target)

    assert (target / "a" / "b" / "term.txt").read_text(encoding="utf-8") == "1\n2\n"
    assert (target / "empty").is_dir()
    Directories.delete(target)
    assert not target.exists()


def test_deletes_a_single_file_and_ignores_missing_paths(tmp_path):
    marker = tmp_path / "prebuilt-json-100.built"
    marker.touch()

    Directories.delete(marker)
    Directories.delete(tmp_path / "missing")

    assert not marker.exists()


def test_counts_the_files_that_pass_a_filter(tmp_path):
    (tmp_path / "1").mkdir()
    (tmp_path / "1" / "header.txt").touch()
    (tmp_path / "1" / "body.txt").touch()

    assert Directories.file_count(tmp_path) == 2
    assert Directories.file_count(tmp_path, lambda file: file.name == "body.txt") == 1
