from __future__ import annotations

try:
    import regex as re_lib
    _PATTERN = r"\p{L}+"
    _FLAGS = re_lib.UNICODE
except ImportError:
    # Fallback for Windows App Control blocking the regex C-extension DLL
    import re as re_lib
    _PATTERN = r"[^\W\d_]+"
    _FLAGS = re_lib.UNICODE

from collections import Counter
from typing import Dict, Iterator, Set

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


class Tokenizer:
    TERM = re_lib.compile(_PATTERN, _FLAGS)
    MIN_TERM_LENGTH = 2

    def __init__(self, stopwords: Set[str]):
        self.stopwords = stopwords

    def occurrences(self, book_id: int, body: str) -> TermOccurrences:
        return TermOccurrences(book_id, self._frequencies(body))

    def _frequencies(self, body: str) -> Dict[str, int]:
        return dict(Counter(self._terms(body)))

    def _terms(self, body: str) -> Iterator[str]:
        for match in self.TERM.finditer(body.lower()):
            term = match.group()
            if self._is_indexable(term):
                yield term

    def _is_indexable(self, term: str) -> bool:
        return len(term) >= self.MIN_TERM_LENGTH and term not in self.stopwords
