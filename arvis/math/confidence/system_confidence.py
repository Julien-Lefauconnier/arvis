# arvis/math/confidence/system_confidence.py

from __future__ import annotations

from dataclasses import dataclass


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@dataclass(frozen=True)
class SystemConfidenceInputs:
    """
    Purely internal mathematical confidence.

    This score must depend only on system-state observables and
    not on any external / human signal.
    """

    delta_w: float | None
    global_safe: bool
    switching_safe: bool
    has_history: bool
    has_observability: bool
    collapse_risk: float = 0.0


def compute_system_confidence(inputs: SystemConfidenceInputs) -> float:
    """
    Bounded confidence score in [0, 1].

    Interpretation:
    - 1.0 => system is well-observed and dynamically coherent
    - 0.0 => system is highly unstable or poorly observable
    """

    score = 1.0

    if inputs.delta_w is not None:
        dw = float(abs(inputs.delta_w))
        score *= 1.0 / (1.0 + dw)
    else:
        score *= 0.7

    if not inputs.global_safe:
        score *= 0.35

    if not inputs.switching_safe:
        score *= 0.75

    if not inputs.has_history:
        score *= 0.60

    if not inputs.has_observability:
        score *= 0.50

    risk = float(inputs.collapse_risk)
    if risk < 0.0:
        risk = 0.0
    if risk > 1.0:
        risk = 1.0

    score *= 1.0 - 0.5 * risk

    return _clamp01(float(score))
