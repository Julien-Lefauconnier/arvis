# arvis/cognition/core/cognitive_core_result.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CognitiveCoreResult:
    """
    Pure scientific output of the cognitive core.
    """

    collapse_risk: float
    dv: float

    # Optional structured outputs
    core_snapshot: Any | None = None
    reflexive_state: Any | None = None

    # Kernel-usable projections
    prev_lyap: Any | None = None
    cur_lyap: Any | None = None
    drift_score: float = 0.0
    regime: str | None = None
    stable: bool | None = None
