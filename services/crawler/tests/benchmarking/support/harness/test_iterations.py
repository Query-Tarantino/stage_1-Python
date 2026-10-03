from typing import List

import pytest

from services.crawler.tests.benchmarking.support.harness.iterations import (
    MICROSECONDS,
    P99,
    SCORE,
    IterationOptions,
    SampledOperations,
    TimedOperations,
    WholeRuns,
)

SHORT = IterationOptions(seconds=0.01)


class RecordedHooks:
    def __init__(self):
        self.calls: List[str] = []

    def setup_iteration(self, measured: bool) -> None:
        self.calls.append(f"setup {measured}")

    def teardown_iteration(self, measured: bool) -> None:
        self.calls.append(f"teardown {measured}")


def test_times_each_whole_run_between_the_hooks_of_its_iteration():
    hooks = RecordedHooks()

    samples = WholeRuns(warm_up=1, measured=2).samples(
        hooks, lambda: hooks.calls.append("run"), SHORT
    )

    assert hooks.calls == [
        "setup False", "run", "teardown False",
        "setup True", "run", "teardown True",
        "setup True", "run", "teardown True",
    ]  # fmt: skip
    assert len(samples[SCORE]) == 2
    assert all(sample >= 0 for sample in samples[SCORE])


def test_discards_the_warm_up_iterations():
    hooks = RecordedHooks()

    samples = TimedOperations(MICROSECONDS, warm_up=3, measured=5).samples(
        hooks, lambda: None, SHORT
    )

    assert hooks.calls.count("setup False") == 3
    assert hooks.calls.count("setup True") == 5
    assert len(samples[SCORE]) == 5


def test_a_run_can_override_the_iterations_every_benchmark_declares():
    quick = IterationOptions(warm_up=1, measured=1, seconds=0.01)
    hooks = RecordedHooks()

    samples = TimedOperations(MICROSECONDS).samples(hooks, lambda: None, quick)

    assert hooks.calls == [
        "setup False", "teardown False", "setup True", "teardown True"
    ]  # fmt: skip
    assert len(samples[SCORE]) == 1


def test_repeats_an_operation_for_the_iteration_and_divides_the_time_by_them():
    operations = []

    samples = TimedOperations(MICROSECONDS, warm_up=0, measured=1).samples(
        RecordedHooks(), lambda: operations.append(1), SHORT
    )

    # A mean time per operation, far below the 10 ms of the iteration
    assert len(operations) > 100
    assert 0 < samples[SCORE][0] < 10_000 / 100


def test_samples_the_mean_and_99th_percentile_of_the_times_of_each_iteration():
    samples = SampledOperations(MICROSECONDS, warm_up=0, measured=2).samples(
        RecordedHooks(), lambda: None, SHORT
    )

    assert set(samples) == {SCORE, P99}
    assert len(samples[SCORE]) == len(samples[P99]) == 2
    assert all(
        mean <= p99 for mean, p99 in zip(samples[SCORE], samples[P99], strict=True)
    )


@pytest.mark.parametrize(
    "times, percentile", [(list(range(1, 101)), 99), (list(range(1, 11)), 10), ([7], 7)]
)
def test_takes_the_nearest_rank_percentile(times, percentile):
    assert SampledOperations.percentile(times[::-1], 99) == percentile
