# arvis/kernel/projection/pi_types.py

from dataclasses import dataclass

# =========================
# X STATE (slow)
# =========================


@dataclass(frozen=True)
class XState:
    cognitive_load: float
    coherence_score: float
    conflict_pressure: float
    uncertainty_mass: float
    decision_commitment: float
    memory_activation: float
    symbolic_stability: float
    retrieval_salience: float


# =========================
# Z STATE (fast dynamics)
# =========================


@dataclass(frozen=True)
class ZDecisionState:
    decision_kind: str | None
    actionability_score: float
    confidence_score: float


@dataclass(frozen=True)
class ZGateState:
    verdict: str
    safety_margin: float
    veto_intensity: float
    confirmation_required: bool


@dataclass(frozen=True)
class ZControlState:
    control_mode: str
    epsilon: float
    beta: float
    exploration_pressure: float


@dataclass(frozen=True)
class ZDynamicState:
    regime: str | None
    temporal_pressure: float
    recent_delta_norm: float
    runtime_instability: float


@dataclass(frozen=True)
class ZState:
    decision: ZDecisionState
    gate: ZGateState
    control: ZControlState
    dynamics: ZDynamicState


# =========================
# Q STATE (modes)
# =========================


@dataclass(frozen=True)
class QState:
    regime_mode: str | None
    gate_mode: str | None
    conversation_mode: str | None
    execution_mode: str | None
    switching_safe: bool


# =========================
# W STATE (perturbations)
# =========================


@dataclass(frozen=True)
class WState:
    uncertainty_pressure: float
    ambiguity_pressure: float
    observation_gap: float
    external_disturbance: float
    projection_residual: float


# =========================
# FINAL Π STATE
# =========================


@dataclass(frozen=True)
class PiState:
    x: XState
    z: ZState
    q: QState
    w: WState
