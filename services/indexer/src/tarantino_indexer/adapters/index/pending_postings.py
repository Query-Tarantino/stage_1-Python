from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple

from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


class PendingPostings:

    def __init__(self):
        self._postings: Dict[str, Set[int]] = defaultdict(set)

    def add(self, occurrences: TermOccurrences) -> None:
        for term in occurrences.frequencies:
            self._postings[term].add(occurrences.book_id)

    def drain(self) -> List[Tuple[str, Set[int]]]:
        drained = sorted(self._postings.items())
        self._postings = defaultdict(set)
        return drained
