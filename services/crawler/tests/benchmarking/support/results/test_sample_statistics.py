import math

import pytest

from services.crawler.tests.benchmarking.support.results.sample_statistics import (
    SampleStatistics,
)

# t(0.975, ν) from the published tables of Student's t
T_975 = {1: 12.7062, 2: 4.3027, 3: 3.1824, 4: 2.7764, 5: 2.5706, 9: 2.2622, 29: 2.0452}


@pytest.mark.parametrize("degrees", sorted(T_975))
def test_finds_the_t_of_the_95_percent_interval(degrees):
    assert SampleStatistics.t_value(0.95, degrees) == pytest.approx(
        T_975[degrees], abs=1e-4
    )


def test_finds_the_t_of_other_confidence_levels():
    # JMH's own Score Error, at 99.9% with 9 samples (SPEC §11)
    assert SampleStatistics.t_value(0.999, 8) == pytest.approx(5.0413, abs=1e-4)


def test_gives_the_half_width_of_the_95_percent_interval_of_the_mean():
    samples = [10.0, 12.0, 11.0, 13.0, 9.0, 11.0]

    error = SampleStatistics.mean_error(samples, 0.95)

    assert SampleStatistics.mean(samples) == pytest.approx(11.0)
    assert error == pytest.approx(2.5706 * math.sqrt(2.0) / math.sqrt(6), abs=1e-4)


def test_cannot_compute_the_error_of_a_single_sample():
    assert math.isnan(SampleStatistics.mean_error([3.0], 0.95))
