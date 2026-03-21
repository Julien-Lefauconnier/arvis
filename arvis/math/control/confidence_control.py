# arvis/math/control/confidence_control.py

from __future__ import annotations

from dataclasses import dataclass


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@dataclass(frozen=True)
class ConfidenceControlInputs:
    system_confidence: float
    base_epsilon: float
    exploration: float


@dataclass(frozen=True)
class ConfidenceControlOutput:
    epsilon: float
    exploration: float
    flags: list[str]


def apply_confidence_control(inputs: ConfidenceControlInputs) -> ConfidenceControlOutput:
    """
    Control layer driven by system confidence.

    IMPORTANT:
    - Does NOT change decision (verdict)
    - Only modulates behavior around it
    """

    conf = _clamp01(float(inputs.system_confidence))

    # -----------------------------------------
    # epsilon modulation (prudence)
    # -----------------------------------------
    epsilon = inputs.base_epsilon * (1.0 + (1.0 - conf))

    # -----------------------------------------
    # exploration modulation
    # -----------------------------------------
    exploration = inputs.exploration * (1.0 + (1.0 - conf))

    flags: list[str] = []

    if conf < 0.3:
        flags.append("low_confidence")

    if conf < 0.15:
        flags.append("very_low_confidence")

    return ConfidenceControlOutput(
        epsilon=float(epsilon),
        exploration=float(exploration),
        flags=flags,
    )