# arvis/cognition/state/cognitive_state.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any

from arvis.signals.signal_journal import SignalJournal


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
    # ------------------------
    # Identity
    # ------------------------
    bundle_id: str

    # ------------------------
    # Stability & math
    # ------------------------
    stability: CognitiveStability
    risk: CognitiveRisk
    control: CognitiveControl
    dynamics: CognitiveDynamics
    projection: Optional[CognitiveProjection]

    # ------------------------
    # Predictive
    # ------------------------
    world_prediction: Optional[Any]
    forecast: Optional[Any]

    # ------------------------
    # Reflexive / IRG
    # ------------------------
    irg: Optional[Any]

    # ------------------------
    # Core outputs
    # ------------------------
    decision: Optional[Any] = None
    trace: Optional[Any] = None
    timeline: Optional[SignalJournal] = None 

    # ------------------------
    # Tools
    # ------------------------
    tool_results: list[Any] = field(default_factory=list)

    # ------------------------
    # IR BRIDGE 
    # ------------------------
    ir_input: Optional[Any] = None
    ir_context: Optional[Any] = None

    # ------------------------
    # IR EXTENSION 
    # ------------------------
    ir_decision: Optional[Any] = None
    ir_state: Optional[Any] = None
    ir_gate: Optional[Any] = None