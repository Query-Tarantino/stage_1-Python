import random
import unicodedata
from collections import Counter
from itertools import groupby

from tarantino_indexer.model.terms.tokenizer import Tokenizer


def test_counts_lowercased_terms_without_stopwords_or_short_tokens():
    tokenizer = Tokenizer({"the", "of"})
    text = "The Island of the island, a SHIPWRECK!"
    term_occurrences = tokenizer.occurrences(1, text)

    assert term_occurrences.frequencies == {"island": 2, "shipwreck": 1}


def test_keeps_accented_letters_and_splits_on_digits_and_apostrophes():
    tokenizer = Tokenizer({"the", "of"})
    text = "Café don't 1984year"
    term_occurrences = tokenizer.occurrences(1, text)

    assert term_occurrences.frequencies == {"café": 1, "don": 1, "year": 1}


def test_measures_term_length_in_code_points():
    term_occurrences = Tokenizer(set()).occurrences(1, "𝒜 𝒜𝒜")

    assert term_occurrences.frequencies == {"𝒜𝒜": 1}


def test_splits_terms_at_numeric_characters_that_are_not_letters():
    term_occurrences = Tokenizer(set()).occurrences(1, "x²y ½ab Ⅻcd ①ef")

    assert term_occurrences.frequencies == {"ab": 1, "cd": 1, "ef": 1}


# Letters, digits, punctuation, combining marks, supplementary letters, numeric
# characters that are not letters, and characters whose lowercase form depends on
# context (final sigma) or changes length (dotted I)
PIECES = [
    "the",
    "The",
    "OF",
    "island",
    "ISLAND",
    "café",
    "cafe\u0301",
    "don't",
    "1984year",
    "x",
    "a",
    "ab",
    "ΟΔΟΣ",
    "λόγος",
    "ΣΑΣ",
    "İstanbul",
    "Straße",
    "STRAẞE",
    "ſhape",
    "Cæsar",
    "漢字",
    "한국어",
    "مرحبا",
    "𝒜",
    "𝒜𝒜",
    "e-mail",
    "rock-and-roll",
    "  ",
    "\n",
    "—",
    "...",
    "123",
    "_",
    "snake_case",
    "\u00a0",
    "Ǆemal",
    "ǅ",
    "x²y",
    "½",
    "Ⅻ",
    "①",
    "\u0301",
]
STOPWORDS = {"the", "of", "σας"}


def test_counts_the_letters_of_unicodedata_like_spec_7():
    tokenizer = Tokenizer(STOPWORDS)
    pieces = random.Random(20261001)
    for _ in range(5000):
        body = "".join(
            pieces.choice(PIECES) + pieces.choice(["", " "])
            for _ in range(pieces.randrange(13))
        )
        assert tokenizer.occurrences(1, body).frequencies == reference(body), body


def reference(body: str) -> dict:
    runs = (
        "".join(letters)
        for is_letter, letters in groupby(
            body.lower(), lambda character: unicodedata.category(character)[0] == "L"
        )
        if is_letter
    )
    return dict(Counter(run for run in runs if len(run) >= 2 and run not in STOPWORDS))
