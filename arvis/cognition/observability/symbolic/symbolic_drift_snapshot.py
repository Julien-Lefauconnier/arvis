# arvis/cognition/observability/symbolic_drift_snapshot.py


from dataclasses import dataclass
from enum import Enum


class SymbolicRegime(str, Enum):
    OK = "ok"
    WARNING = "warning"
    DRIFT = "drift"
    CONTRADICTION = "contradiction"


@dataclass(frozen=True)
class SymbolicDriftSnapshot:
    drift_score: float
    regime: SymbolicRegime
    intent_switch: bool
    gate_switch: bool
    confidence_delta: float
    conflict_delta: float
    override_rate: float
