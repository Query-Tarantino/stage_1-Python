import hashlib
import unicodedata
from pathlib import Path

from tarantino_indexer.adapters.index.folders.term_files import TermFiles

ROOT = Path("index")


def test_keeps_ascii_lowercase_terms_readable_under_their_first_letter():
    assert TermFiles.file(ROOT, "whale") == ROOT / "w" / "whale.txt"


def test_encodes_every_other_utf8_byte_and_uses_the_first_code_point_as_directory():
    assert TermFiles.file(ROOT, "écume") == ROOT / "%C3%A9" / "%C3%A9cume.txt"
    assert TermFiles.file(ROOT, "𝒜b") == ROOT / "%F0%9D%92%9C" / "%F0%9D%92%9Cb.txt"


def test_names_terms_that_only_differ_in_case_folding_or_normalization_differently():
    assert TermFiles.file(ROOT, "shape") != TermFiles.file(ROOT, "ſhape")
    assert TermFiles.file(ROOT, unicodedata.normalize("NFC", "café")) != TermFiles.file(
        ROOT, unicodedata.normalize("NFD", "café")
    )


def test_hashes_names_longer_than_200_characters():
    long_term = "漢" * 100
    sha256 = hashlib.sha256(long_term.encode("utf-8")).hexdigest()

    assert TermFiles.file(ROOT, long_term) == ROOT / "%E6%BC%A2" / f"#{sha256}.txt"
    assert TermFiles.file(ROOT, "l" * 200) == ROOT / "l" / ("l" * 200 + ".txt")
