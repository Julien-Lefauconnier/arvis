# arvis/cognition/gate/gate_decision_trace.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GateDecisionTraceStep:
    stage: str
    before: str
    after: str
    reason_codes: tuple[str, ...]
    severity: float = 0.0
    stability_impact: float = 0.0
    input_snapshot: dict[str, Any] | None = None


@dataclass(frozen=True)
class GateDecisionTrace:
    steps: tuple[GateDecisionTraceStep, ...]
    # --- EXTENDED (non-normative) ---
    # NOTE:
    # Only `steps` is normative (spec-aligned).
    # All other fields are extended observability metrics.
    total_severity: float = 0.0
    max_severity: float = 0.0
    instability_score: float = 0.0
