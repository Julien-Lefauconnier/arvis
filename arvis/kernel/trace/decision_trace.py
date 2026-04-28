# arvis/kernel/trace/decision_trace.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from arvis.cognition.gate.cognitive_gate_result import CognitiveGateResult
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationResult
from arvis.action.action_decision import ActionDecision
from arvis.cognition.execution.executable_intent import ExecutableIntent


@dataclass(frozen=True)
class DecisionTrace:
    """
    Canonical trace of a cognitive decision.

    ZKCS-compliant:
    - immutable
    - no side effects
    - no external dependency
    """

    timestamp: datetime
    user_id: str

    # Core cognition
    gate_result: CognitiveGateResult

    # Optional layers
    confirmation_request: Optional[ConfirmationRequest] = None
    confirmation_result: Optional[ConfirmationResult] = None

    action_decision: Optional[ActionDecision] = None
    executable_intent: Optional[ExecutableIntent] = None
    conflict: Optional[Any] = None
    # Observability
    predictive: Optional[Any] = None
    stability: Optional[Any] = None
    symbolic: Optional[Any] = None
    system_tension: Optional[Any] = None
    quadratic_lyapunov: Optional[Any] = None
    quadratic_comparability: Optional[Any] = None
    theoretical_regime: Optional[Any] = None
    fast_dynamics: Optional[Any] = None
    perturbation: Optional[Any] = None

    conversation: Optional[Any] = None
    governance: Optional[Any] = None
    pending_actions: Optional[Any] = None
    events: Optional[Any] = None
    coherence_policy: Optional[Any] = None
    memory_influence: Optional[dict[str, Any]] = None
