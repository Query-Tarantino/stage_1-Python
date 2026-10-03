import random
import unicodedata
from itertools import groupby

from tarantino_query.model.query_terms import QueryTerms


def test_normalizes_like_the_indexer_and_removes_duplicates():
    terms = QueryTerms.of("The ISLAND of a Shipwreck island", {"the", "of"})
    assert terms == ["island", "shipwreck"]


def test_keeps_the_order_in_which_terms_first_appear():
    assert QueryTerms.of("whale island ship WHALE", set()) == [
        "whale",
        "island",
        "ship",
    ]


def test_splits_terms_at_numeric_characters_that_are_not_letters():
    assert QueryTerms.of("x²y ½ab Ⅻcd ①ef", set()) == ["ab", "cd", "ef"]


PIECES = [
    "the",
    "Island",
    "café",
    "cafe\u0301",
    "don't",
    "1984year",
    "x",
    "ab",
    "ΟΔΟΣ",
    "İstanbul",
    "Straße",
    "ſhape",
    "漢字",
    "𝒜𝒜",
    "e-mail",
    " ",
    "—",
    "_",
    "\u00a0",
    "x²y",
    "½",
    "Ⅻ",
    "①",
    "\u0301",
]


def test_finds_the_letters_of_unicodedata_like_spec_7():
    pieces = random.Random(20261003)
    for _ in range(2000):
        query = "".join(
            pieces.choice(PIECES) + pieces.choice(["", " "]) for _ in range(8)
        )
        assert QueryTerms.of(query, {"the"}) == reference(query), query


def reference(query: str) -> list:
    runs = (
        "".join(letters)
        for is_letter, letters in groupby(
            query.lower(), lambda character: unicodedata.category(character)[0] == "L"
        )
        if is_letter
    )
    return list(dict.fromkeys(run for run in runs if len(run) >= 2 and run != "the"))
