import re
from itertools import groupby
from typing import Iterator, List, Set


class QueryTerms:
    _WORD = re.compile(r"[^\W\d_]+")
    _MIN_TERM_LENGTH = 2

    @staticmethod
    def of(query: str, stopwords: Set[str]) -> List[str]:
        terms = QueryTerms._letter_runs(query.lower())
        filtered_terms = (
            term for term in terms if QueryTerms._is_searchable(term, stopwords)
        )
        return list(
            dict.fromkeys(filtered_terms)
        )

    @staticmethod
    def _letter_runs(text: str) -> Iterator[str]:
        for match in QueryTerms._WORD.finditer(text):
            run = match.group()
            if run.isalpha():
                yield run
            else:
                groups = groupby(run, str.isalpha)
                yield from (
                    "".join(letters) for is_letter, letters in groups if is_letter
                )

    @staticmethod
    def _is_searchable(term: str, stopwords: Set[str]) -> bool:
        return len(term) >= QueryTerms._MIN_TERM_LENGTH and term not in stopwords
