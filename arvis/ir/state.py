# arvis/ir/state.py

from dataclasses import dataclass, field
from typing import Any, Optional


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
    version: str = field(default="1.0", init=False)
    state_id: str
    bundle_id: str

    dv: float
    collapse_risk: CognitiveRiskIR

    epsilon: float
    early_warning: bool

    world_prediction: Any | None = None
    forecast: Any | None = None
    irg: Any | None = None
    regime: Optional[str] = None
    stable: Optional[bool] = None

    system_tension: Optional[float] = None
    drift: Optional[float] = None

    projection_valid: Optional[bool] = None
    projection_margin: Optional[float] = None
    