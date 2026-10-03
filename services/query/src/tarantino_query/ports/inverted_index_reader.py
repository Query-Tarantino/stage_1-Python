from typing import Protocol, Set


class InvertedIndexReader(Protocol):
    def postings(self, term: str) -> Set[int]: ...
