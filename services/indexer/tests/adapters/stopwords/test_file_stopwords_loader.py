import pytest

from tarantino_indexer.adapters.stopwords.file_stopwords_loader import (
    FileStopwordsLoader,
)


def test_strips_and_lowercases_entries_ignoring_blank_lines(tmp_path):
    file = tmp_path / "stopwords.txt"
    file.write_bytes(b" The \n\nOF\r\nand\n")

    assert FileStopwordsLoader(file).stopwords() == {"the", "of", "and"}


def test_strips_only_the_whitespace_java_strips(tmp_path):
    file = tmp_path / "stopwords.txt"
    file.write_bytes("\u00a0the\u3000\n".encode("utf-8"))

    assert FileStopwordsLoader(file).stopwords() == {"\u00a0the"}


def test_ends_lines_only_at_line_feeds(tmp_path):
    file = tmp_path / "stopwords.txt"
    file.write_bytes("the\u2028of\u0085and\n".encode("utf-8"))

    assert FileStopwordsLoader(file).stopwords() == {"the\u2028of\u0085and"}


def test_fails_without_a_stopwords_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        FileStopwordsLoader(tmp_path / "stopwords.txt").stopwords()
