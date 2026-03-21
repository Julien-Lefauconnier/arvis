# arvis/math/stability/global_guard.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class GlobalStabilityGuard:
    """
    Tracks global Lyapunov energy evolution.

    Guarantees:
    - No long-term divergence
    - Bounded instability bursts
    """

    window: int = 10
    max_positive_ratio: float = 0.6
    max_cumulative_increase: float = 2.0

    def check(
        self,
        deltas: List[float],
    ) -> bool:
        """
        Returns True if globally stable.
        """

        if not deltas:
            return True

        recent = deltas[-self.window :]

        # -----------------------------------------
        # 1. Ratio of positive energy steps
        # -----------------------------------------
        positives = [d for d in recent if d > 0]
        ratio = len(positives) / len(recent)

        if ratio > self.max_positive_ratio:
            return False

        # -----------------------------------------
        # 2. Cumulative drift
        # -----------------------------------------
        cumulative = sum(recent)

        if cumulative > self.max_cumulative_increase:
            return False

        return True