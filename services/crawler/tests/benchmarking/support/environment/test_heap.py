import tracemalloc

from services.crawler.tests.benchmarking.support.environment.heap import Heap

MEGABYTE = 1024 * 1024


def test_measures_what_the_result_of_a_build_retains():
    retained, kept = Heap.retained_by(lambda: bytearray(MEGABYTE))

    assert len(kept) == MEGABYTE
    assert MEGABYTE <= retained < 2 * MEGABYTE


def test_leaves_out_the_garbage_of_the_build():
    def build():
        garbage = [bytearray(MEGABYTE) for _ in range(5)]
        return len(garbage)

    retained, _ = Heap.retained_by(build)

    assert retained < MEGABYTE


def test_traces_only_around_the_measure():
    Heap.retained_by(lambda: None)

    assert not tracemalloc.is_tracing()
