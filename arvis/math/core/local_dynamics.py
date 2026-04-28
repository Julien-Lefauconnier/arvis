# arvis/math/core/local_dynamics.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


@dataclass(frozen=True)
class LocalDynamicsSample:
    delta_v: float
    features: Dict[str, float]


class LocalCognitiveDynamics:
    """
    Empirical local dynamics estimator.

    Stores recent (delta_V, features) samples and computes a simple
    sensitivity score per feature.

    IMPORTANT:
    - ZKCS-safe: stores only numerical summaries (no content).
    - Non-blocking: estimate returns None until enough samples.
    """

    def __init__(self, window: int = 30, min_samples: int = 5):
        if window <= 0:
            raise ValueError("window must be > 0")
        if min_samples <= 0:
            raise ValueError("min_samples must be > 0")

        self._history: Deque[LocalDynamicsSample] = deque(maxlen=window)
        self._min_samples = min_samples

    def push(self, delta_v: float, features: Dict[str, float]) -> None:
        # defensive copy: avoid external mutation of dict
        self._history.append(LocalDynamicsSample(float(delta_v), dict(features)))

    def size(self) -> int:
        return len(self._history)

    def estimate_sensitivity(self) -> Optional[Dict[str, float]]:
        """
        Returns a naive empirical sensitivity:
          sens[k] = mean(|delta_v| * |feature_k|) over window

        It’s crude but useful:
        - highlights which features correlate with instability
        - feeds future calibration/controls

        Returns None until min_samples reached.
        """
        if len(self._history) < self._min_samples:
            return None

        accum: Dict[str, float] = {}
        n = len(self._history)

        for sample in self._history:
            dv = abs(sample.delta_v)
            for k, v in sample.features.items():
                accum[k] = accum.get(k, 0.0) + (dv * abs(float(v)))

        return {k: val / n for k, val in accum.items()}
