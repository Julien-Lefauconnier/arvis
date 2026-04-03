# arvis/cognition/state/cognitive_state.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any


# ------------------------
# Sub-blocks
# ------------------------

@dataclass(frozen=True)
class CognitiveStability:
    dv: float
    regime: Optional[str]
    stable: Optional[bool]


@dataclass(frozen=True)
class CognitiveRisk:
    mh_risk: float
    world_risk: float
    forecast_risk: float
    fused_risk: float
    smoothed_risk: float
    early_warning: bool


@dataclass(frozen=True)
class CognitiveControl:
    epsilon: float


@dataclass(frozen=True)
class CognitiveDynamics:
    system_tension: Optional[float]
    drift: Optional[float]


@dataclass(frozen=True)
class CognitiveProjection:
    valid: Optional[bool]
    margin: Optional[float]


# ------------------------
# Main state
# ------------------------

@dataclass(frozen=True)
class CognitiveState:
    """
    CognitiveState V1 (structured, ZKCS-safe)
    """

    bundle_id: str

    stability: CognitiveStability
    risk: CognitiveRisk
    control: CognitiveControl
    dynamics: CognitiveDynamics
    projection: Optional[CognitiveProjection]

    world_prediction: Optional[Any]
    forecast: Optional[Any]

    irg: Optional[Any]
    tool_results: list[Any] = field(default_factory=list)