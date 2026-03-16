# arvis/math/risk/risk_calibration.py

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Tuple

# tests + core share the exact same parameters.
DEFAULT_RISK_CALIBRATION: Dict[str, Tuple[float, float]] = {
    "mh": (0.55, 6.0),
    "wm": (0.60, 6.0),
    "forecast": (0.50, 4.0),
}

def clamp01(x: float) -> float:
    try:
        v = float(x)
    except Exception:
        return 0.0
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def sigmoid(x: float) -> float:
    """
    Numerically stable sigmoid.
    """
    # Avoid overflow for large magnitude values.
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def calibrate_risk(r: float, *, theta: float, k: float) -> float:
    """
    Calibrate a raw risk r ∈ [0,1] into a probability via:

        p = sigmoid(k * (r - theta))

    Invariants:
    - r ∈ [0,1]
    - p ∈ (0,1)
    - monotone in r if k ≥ 0
    - |∂p/∂r| ≤ k/4
    """
    r = clamp01(r)
    theta = clamp01(theta)
    k = float(k)

    if k <= 0.0:
        # Degenerate case: no slope => constant 0.5
        return 0.5

    return sigmoid(k * (r - theta))


def probabilistic_or(probs: Iterable[float]) -> float:
    """
    Probabilistic OR:

        P = 1 - Π(1 - p_i)

    Invariants:
    - If p_i ∈ [0,1], then P ∈ [0,1]
    - Monotone in each p_i
    """
    prod = 1.0
    has_any = False
    for p in probs:
        has_any = True
        p = clamp01(p)
        prod *= (1.0 - p)

    if not has_any:
        return 0.0

    return clamp01(1.0 - prod)


def calibrated_or_fusion(
    sources: Iterable[Tuple[str, float]],
    *,
    calibration: Dict[str, Tuple[float, float]],
) -> float:
    """
    sources: iterable of (name, raw_risk)
    calibration: name -> (theta, k)

    For each source:
        p_i = sigmoid(k_i * (r_i - theta_i))

    Then:
        R = 1 - Π(1 - p_i)

    Unknown sources default to (theta=0.5, k=4.0).
    """
    probs = []

    for name, raw_risk in sources:
        theta, k = calibration.get(name, (0.5, 4.0))
        p = calibrate_risk(raw_risk, theta=theta, k=k)
        probs.append(p)

    return probabilistic_or(probs)