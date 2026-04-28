# arvis/math/gate/gate_types.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


@dataclass
class GateKernelInputs:
    # Lyapunov
    prev_lyap: Optional[Any]
    cur_lyap: Optional[Any]

    # Slow / symbolic
    slow_prev: Optional[Any]
    slow_cur: Optional[Any]
    symbolic_prev: Optional[Any]
    symbolic_cur: Optional[Any]

    # Stability signals
    collapse_risk: float
    stable: Optional[bool]

    # Switching
    switching_safe: bool

    # Global
    global_safe: bool

    # Metrics
    delta_w: Optional[float]
    w_prev: Optional[float]
    w_current: Optional[float]

    # Adaptive
    adaptive_margin: Optional[float]
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
    certificate: Dict[str, bool]
