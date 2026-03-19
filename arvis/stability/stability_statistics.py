# arvis/stability/stability_statistics.py

from collections import deque
from dataclasses import dataclass
from typing import Deque


@dataclass(frozen=True)
class StabilityStatsSnapshot:
    mean_delta: float
    contraction_rate: float
    instability_rate: float
    samples: int


class StabilityStatistics:
    """
    Global statistical observer of cognitive stability.

    Kernel primitive.
    ZKCS compliant: only mathematical signals.
    """

    def __init__(self, window: int = 500):
        self.window = window
        self._buffer: Deque[float] = deque(maxlen=window)

    def push(self, delta_v: float) -> None:
        self._buffer.append(delta_v)

    def snapshot(self) -> StabilityStatsSnapshot:

        if not self._buffer:
            return StabilityStatsSnapshot(0.0, 0.0, 0.0, 0)

        n = len(self._buffer)

        mean = sum(self._buffer) / n

        contraction = sum(1 for x in self._buffer if x < 0) / n
        instability = sum(1 for x in self._buffer if x > 0) / n

        return StabilityStatsSnapshot(
            mean_delta=mean,
            contraction_rate=contraction,
            instability_rate=instability,
            samples=n,
        )
    
    def compute(self, snapshot: StabilityStatsSnapshot) -> StabilityStatsSnapshot:
        """
        Compute stability statistics from a projected snapshot.

        For now:
        - acts as pass-through
        - ensures compatibility with pipeline/tests

        Future:
        - aggregate metrics
        - compute trends
        - derive risk envelopes
        """

        return snapshot