# arvis/cognition/control/cognitive_control_snapshot.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.core.normalization import clamp01
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


@dataclass(frozen=True)
class CognitiveControlSnapshot:
    """
    Final full control snapshot for ARVIS kernel.

    Immutable, declarative, kernel-safe.
    """

    gate_mode: CognitiveMode
    epsilon: float
    smoothed_risk: float
    lyap_verdict: LyapunovVerdict

    # Optional observability outputs
    exploration: Any | None = None
    drift: Any | None = None
    regime: Any | None = None
    calibration: Any | None = None
    temporal_pressure: Any | None = None
    temporal_modulation: Any | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "epsilon", max(0.0, float(self.epsilon)))
        object.__setattr__(self, "smoothed_risk", clamp01(self.smoothed_risk))
