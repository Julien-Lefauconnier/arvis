# arvis/math/drift/drift.py

from __future__ import annotations

from typing import Iterable, Set
from math import isfinite

from arvis.math.core.normalization import clamp01


def l1_distance01(x: Iterable[float], y: Iterable[float]) -> float:
    """
    L1 distance on normalized vectors in [0,1].
    Output also in [0,1].
    """
    xs = list(x)
    ys = list(y)

    if len(xs) != len(ys):
        raise ValueError("Vectors must have same length")

    if not xs:
        return 0.0

    s = 0.0
    for a, b in zip(xs, ys):
        if not (isfinite(a) and isfinite(b)):
            continue
        s += abs(a - b)

    return clamp01(s / len(xs))


def jaccard_distance(a: Set[str], b: Set[str]) -> float:
    """
    Jaccard distance for symbolic sets.
    """
    if not a and not b:
        return 0.0

    inter = len(a.intersection(b))
    union = len(a.union(b))

    if union == 0:
        return 0.0

    return 1.0 - inter / union


def hybrid_drift(
    *,
    continuous_a: Iterable[float],
    continuous_b: Iterable[float],
    symbolic_a: Set[str],
    symbolic_b: Set[str],
    alpha: float = 0.5,
) -> float:
    """
    Hybrid declarative drift.

    alpha:
        0 → purely symbolic
        1 → purely continuous
    """

    alpha = clamp01(alpha)

    d_cont = l1_distance01(continuous_a, continuous_b)
    d_sym = jaccard_distance(symbolic_a, symbolic_b)

    return clamp01(alpha * d_cont + (1 - alpha) * d_sym)
