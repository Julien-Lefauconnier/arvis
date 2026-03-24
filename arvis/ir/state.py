# arvis/ir/state.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CognitiveRiskIR:
    mh_risk: float
    world_risk: float
    forecast_risk: float
    fused_risk: float
    smoothed_risk: float


@dataclass(frozen=True)
class CognitiveStateIR:
    """
    Canonical cognitive state snapshot.
    """

    state_id: str
    bundle_id: str

    dv: float
    collapse_risk: CognitiveRiskIR

    epsilon: float
    early_warning: bool

    world_prediction: Any | None = None
    forecast: Any | None = None
    irg: Any | None = None