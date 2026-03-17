# arvis/cognition/core/cognitive_core_result.py

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CognitiveCoreResult:
    """
    Pure scientific output of the cognitive core.
    """

    collapse_risk: float
    dv: float

    # Optional structured outputs
    core_snapshot: Optional[Any] = None
    reflexive_state: Optional[Any] = None

    # Kernel-usable projections
    prev_lyap: Optional[Any] = None
    cur_lyap: Optional[Any] = None
    drift_score: float = 0.0
    regime: Optional[str] = None
    stable: Optional[bool] = None