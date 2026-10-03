from __future__ import annotations

import re
from collections import Counter
from itertools import groupby
from typing import Dict, Iterator, Set

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


class Tokenizer:
    WORD = re.compile(r"[^\W\d_]+")
    MIN_TERM_LENGTH = 2

    def __init__(self, stopwords: Set[str]):
        self.stopwords = stopwords

    def occurrences(self, book_id: int, body: str) -> TermOccurrences:
        return TermOccurrences(book_id, self._frequencies(body))

    def _frequencies(self, body: str) -> Dict[str, int]:
        return dict(Counter(self._terms(body)))

    def _terms(self, body: str) -> Iterator[str]:
        for term in self._letter_runs(body.lower()):
            if self._is_indexable(term):
                yield term

    @classmethod
    def _letter_runs(cls, text: str) -> Iterator[str]:
        for match in cls.WORD.finditer(text):
            run = match.group()
            if run.isalpha():
                yield run
            else:
                groups = groupby(run, str.isalpha)
                yield from (
                    "".join(letters) for is_letter, letters in groups if is_letter
                )

    def _is_indexable(self, term: str) -> bool:
        return len(term) >= self.MIN_TERM_LENGTH and term not in self.stopwords
