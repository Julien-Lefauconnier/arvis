# arvis/cognition/observability/symbolic_state.py

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SymbolicState:
    intent_type: str
    intent_confidence: float

    gate_verdict: str
    conversation_mode: str

    conflict_histogram: Dict[str, int]
    conflict_severity: float

    override_count: int
    override_rate: float
