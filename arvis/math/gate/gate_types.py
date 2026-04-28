# arvis/math/gate/gate_types.py

from dataclasses import dataclass
from typing import Any

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


@dataclass
class GateKernelInputs:
    # Lyapunov
    prev_lyap: Any | None
    cur_lyap: Any | None

    # Slow / symbolic
    slow_prev: Any | None
    slow_cur: Any | None
    symbolic_prev: Any | None
    symbolic_cur: Any | None

    # Stability signals
    collapse_risk: float
    stable: bool | None

    # Switching
    switching_safe: bool

    # Global
    global_safe: bool

    # Metrics
    delta_w: float | None
    w_prev: float | None
    w_current: float | None

    # Adaptive
    adaptive_margin: float | None
    adaptive_available: bool

    # Runtime
    cognitive_mode: Any
    epsilon: float


@dataclass
class GateKernelResult:
    pre_verdict: LyapunovVerdict
    final_verdict: LyapunovVerdict

    # Observability
    recovery_detected: bool
    adaptive_block: bool

    # Reasoning trace (math-only)
    reasons: list[str]

    # Certificate
    certificate: dict[str, bool]
