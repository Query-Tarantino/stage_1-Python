from __future__ import annotations

import math
import statistics
from typing import Sequence


class SampleStatistics:
    BISECTION_STEPS = 100

    @staticmethod
    def mean(samples: Sequence[float]) -> float:
        return statistics.fmean(samples)

    @staticmethod
    def mean_error(samples: Sequence[float], confidence: float) -> float:
        if len(samples) < 2:
            return math.nan
        t = SampleStatistics.t_value(confidence, len(samples) - 1)
        return t * statistics.stdev(samples) / math.sqrt(len(samples))

    @staticmethod
    def t_value(confidence: float, degrees: int) -> float:
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
