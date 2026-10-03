try:
    import regex as re_lib
    _PATTERN = r"\p{L}+"
    _FLAGS = re_lib.UNICODE
except ImportError:
    # Fallback for Windows App Control blocking the regex C-extension DLL
    import re as re_lib
    _PATTERN = r"[^\W\d_]+"
    _FLAGS = re_lib.UNICODE

from typing import Set


class QueryTerms:
    _TERM = re_lib.compile(_PATTERN, _FLAGS)
    _MIN_TERM_LENGTH = 2

    @staticmethod
    def of(query: str, stopwords: Set[str]) -> Set[str]:
        terms = (match.group(0) for match in QueryTerms._TERM.finditer(query.lower()))
        filtered_terms = (
            term for term in terms if QueryTerms._is_searchable(term, stopwords)
        )
        return set(dict.fromkeys(filtered_terms))  # ordered deduplication

    @staticmethod
    def _is_searchable(term: str, stopwords: Set[str]) -> bool:
        return len(term) >= QueryTerms._MIN_TERM_LENGTH and term not in stopwords
