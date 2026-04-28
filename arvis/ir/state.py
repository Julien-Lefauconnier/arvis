# arvis/ir/state.py

from dataclasses import dataclass, field
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
    regime: str | None = None
    stable: bool | None = None

    system_tension: float | None = None
    drift: float | None = None

    projection_valid: bool | None = None
    projection_margin: float | None = None

    # -----------------------------------------
    # TOOL EXECUTION
    # -----------------------------------------
    tool_results: list[dict[str, object]] | None = None
