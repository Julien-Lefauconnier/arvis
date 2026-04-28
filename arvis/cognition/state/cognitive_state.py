# arvis/cognition/state/cognitive_state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from arvis.signals.signal_journal import SignalJournal

# ------------------------
# Sub-blocks
# ------------------------


@dataclass(frozen=True)
class CognitiveStability:
    dv: float
    regime: str | None
    stable: bool | None


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
    system_tension: float | None
    drift: float | None


@dataclass(frozen=True)
class CognitiveProjection:
    valid: bool | None
    margin: float | None


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
    projection: CognitiveProjection | None

    # ------------------------
    # Predictive
    # ------------------------
    world_prediction: Any | None
    forecast: Any | None

    # ------------------------
    # Reflexive / IRG
    # ------------------------
    irg: Any | None

    # ------------------------
    # Core outputs
    # ------------------------
    decision: Any | None = None
    trace: Any | None = None
    timeline: SignalJournal | None = None

    # ------------------------
    # Tools
    # ------------------------
    tool_results: list[Any] = field(default_factory=list)

    # ------------------------
    # IR BRIDGE
    # ------------------------
    ir_input: Any | None = None
    ir_context: Any | None = None

    # ------------------------
    # IR EXTENSION
    # ------------------------
    ir_decision: Any | None = None
    ir_state: Any | None = None
    ir_gate: Any | None = None
