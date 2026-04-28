# arvis/math/stability/regime_estimator.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RegimeSnapshot:
    regime: str
    confidence: float
    variance: float


class CognitiveRegimeEstimator:
    """
    Empirical regime detection.

    Detects:
    - stable
    - oscillatory
    - critical
    - chaotic
    - transition
    """

    def __init__(self, window: int = 40, min_samples: int = 10):
        if window <= 0:
            raise ValueError("window must be > 0")
        if min_samples <= 0:
            raise ValueError("min_samples must be > 0")

        self._history: deque[float] = deque(maxlen=window)
        self._min_samples = min_samples

    def push(self, delta_v: float) -> RegimeSnapshot | None:
        self._history.append(float(delta_v))

        if len(self._history) < self._min_samples:
            return None

        values = list(self._history)

        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)

        contraction = sum(1 for x in values if x < 0) / len(values)

        # -----------------------
        # Simple regime heuristic
        # -----------------------

        if contraction > 0.9 and var < 0.01:
            regime = "stable"
            conf = 0.9

        elif contraction > 0.7 and var < 0.1:
            regime = "oscillatory"
            conf = 0.7

        elif contraction > 0.5:
            regime = "critical"
            conf = 0.6

        elif var > 0.2:
            regime = "chaotic"
            conf = 0.8

        else:
            regime = "transition"
            conf = 0.5

        return RegimeSnapshot(
            regime=regime,
            confidence=conf,
            variance=var,
        )
