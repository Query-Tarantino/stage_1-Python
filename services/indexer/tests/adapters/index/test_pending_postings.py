from tarantino_indexer.adapters.index.pending_postings import PendingPostings
from tarantino_indexer.model.terms.term_occurrences import TermOccurrences


def test_are_emptied_when_drained():
    pending = PendingPostings()
    pending.add(TermOccurrences(5, {"island": 1}))
    pending.add(TermOccurrences(1342, {"island": 2}))

    assert pending.drain() == [("island", {5, 1342})]
    assert pending.drain() == []


def test_are_drained_in_term_order():
    pending = PendingPostings()
    pending.add(TermOccurrences(5, {"whale": 1, "island": 1, "écume": 1, "ahab": 1}))

    assert [term for term, _ in pending.drain()] == ["ahab", "island", "whale", "écume"]
