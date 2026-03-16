# arvis/math/core/normalization.py

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, tanh
from typing import Iterable


EPS = 1e-12


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x to [lo, hi]. NaN/inf -> lo (conservative)."""
    if not isfinite(x):
        return lo
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def clamp01(x: float) -> float:
    return clamp(x, 0.0, 1.0)


def safe_div(num: float, den: float, default: float = 0.0) -> float:
    """Safe division. If den is 0 or non-finite => default."""
    if not isfinite(num) or not isfinite(den) or abs(den) < EPS:
        return default
    return num / den


def sigmoid01(x: float, *, k: float = 1.0) -> float:
    """
    Squash real x to (0,1) with sigmoid.
    Conservative behavior for non-finite -> 0.0.
    """
    if not isfinite(x) or not isfinite(k) or k <= 0:
        return 0.0
    # Avoid overflow
    z = clamp(-k * x, -60.0, 60.0)
    return 1.0 / (1.0 + exp(z))


def tanh01(x: float, *, k: float = 1.0) -> float:
    """
    Squash real x to (0,1) via tanh.
    """
    if not isfinite(x) or not isfinite(k) or k <= 0:
        return 0.0
    z = k * x
    # tanh is stable but clamp anyway for safety
    z = clamp(z, -60.0, 60.0)
    return 0.5 * (tanh(z) + 1.0)


def affine01(x: float, *, x_min: float, x_max: float, default: float = 0.0) -> float:
    """
    Map x from [x_min, x_max] to [0,1] linearly then clamp.
    If bounds invalid => default.
    """
    if not (isfinite(x) and isfinite(x_min) and isfinite(x_max)):
        return default
    if x_max - x_min < EPS:
        return default
    t = (x - x_min) / (x_max - x_min)
    return clamp01(t)


def normalize_weights(weights: Iterable[float]) -> list[float]:
    """
    Normalize non-negative weights to sum=1.
    Negative / non-finite weights become 0.
    If all zero => uniform.
    """
    ws = []
    for w in weights:
        if not isfinite(w) or w < 0:
            ws.append(0.0)
        else:
            ws.append(float(w))

    s = sum(ws)
    if s < EPS:
        n = len(ws)
        if n == 0:
            return []
        return [1.0 / n] * n
    return [w / s for w in ws]


def weighted_sum01(values01: Iterable[float], weights: Iterable[float]) -> float:
    """
    Weighted sum of values already in [0,1], with normalized weights.
    Output guaranteed in [0,1].
    """
    vals = [clamp01(v) for v in values01]
    ws = normalize_weights(weights)
    if len(vals) != len(ws):
        raise ValueError("values and weights must have same length")
    s = 0.0
    for v, w in zip(vals, ws):
        s += v * w
    return clamp01(s)


def budget_ratio01(current: float, maximum: float) -> float:
    """
    Budget usage ratio in [0,1]. If maximum <=0 => 1 (fully consumed).
    """
    if not isfinite(current) or not isfinite(maximum):
        return 1.0
    if maximum <= 0:
        return 1.0
    return clamp01(current / maximum)


@dataclass(frozen=True)
class NormalizedSignals:
    """
    Canonical normalized container for ARVIS math layer.
    Everything MUST be in [0,1].
    """
    risk: float
    drift: float
    uncertainty: float
    budget_used: float

    def __post_init__(self):
        object.__setattr__(self, "risk", clamp01(self.risk))
        object.__setattr__(self, "drift", clamp01(self.drift))
        object.__setattr__(self, "uncertainty", clamp01(self.uncertainty))
        object.__setattr__(self, "budget_used", clamp01(self.budget_used))