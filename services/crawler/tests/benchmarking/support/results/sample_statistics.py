from __future__ import annotations

import math
import statistics
from typing import Sequence


class SampleStatistics:
    # The mean of the samples and the half-width of its confidence interval,
    # t(1 - (1 - confidence) / 2, n - 1) · s / √n (SPEC §11), as JMH's ListStatistics
    # computes them with Apache Commons Math; the standard library has no Student's t
    BISECTION_STEPS = 100

    @staticmethod
    def mean(samples: Sequence[float]) -> float:
        return statistics.fmean(samples)

    @staticmethod
    def mean_error(samples: Sequence[float], confidence: float) -> float:
        # Unknown with fewer than 2 samples (SPEC §11)
        if len(samples) < 2:
            return math.nan
        t = SampleStatistics.t_value(confidence, len(samples) - 1)
        return t * statistics.stdev(samples) / math.sqrt(len(samples))

    @staticmethod
    def t_value(confidence: float, degrees: int) -> float:
        # The t at which P(|T| ≤ t) = confidence, by bisection on θ = atan(t / √ν),
        # in which that probability increases from 0 at θ = 0 to 1 at θ = π/2
        low, high = 0.0, math.pi / 2
        for _ in range(SampleStatistics.BISECTION_STEPS):
            middle = (low + high) / 2
            if SampleStatistics._central_probability(middle, degrees) < confidence:
                low = middle
            else:
                high = middle
        return math.sqrt(degrees) * math.tan((low + high) / 2)

    @staticmethod
    def _central_probability(theta: float, degrees: int) -> float:
        # P(|T| ≤ √ν tan θ) for ν degrees of freedom, in the closed form of Student's
        # t for a whole ν: a finite series of powers of cos θ
        sine, cosine = math.sin(theta), math.cos(theta)
        if degrees % 2 == 0:
            term, total = 1.0, 1.0
            for k in range(1, degrees // 2):
                term *= (2 * k - 1) / (2 * k) * cosine**2
                total += term
            return sine * total
        if degrees == 1:
            return 2 * theta / math.pi
        term, total = cosine, cosine
        for k in range(1, (degrees - 1) // 2):
            term *= 2 * k / (2 * k + 1) * cosine**2
            total += term
        return 2 / math.pi * (theta + sine * total)
