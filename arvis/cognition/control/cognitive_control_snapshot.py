# arvis/cognition/control/cognitive_control_snapshot.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from arvis.math.control.eps_adaptive import CognitiveMode
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
    exploration: Optional[Any] = None
    drift: Optional[Any] = None
    regime: Optional[Any] = None
    calibration: Optional[Any] = None
    temporal_pressure: Optional[Any] = None
    temporal_modulation: Optional[Any] = None