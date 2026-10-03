import re
from itertools import groupby
from typing import Iterator, List, Set


class QueryTerms:
    # A term is a maximal run of letters, Unicode category L (SPEC §7), which is what
    # str.isalpha() tests. _WORD finds them with the standard re module, in the Unicode
    # version of the runtime; its runs may also hold numeric characters that are not
    # letters, such as ² or ½, which _letter_runs splits off.
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
        )  # distinct, in order of first appearance

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
