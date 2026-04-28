# arvis/kernel/trace/decision_trace.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from arvis.action.action_decision import ActionDecision
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationResult
from arvis.cognition.execution.executable_intent import ExecutableIntent
from arvis.cognition.gate.cognitive_gate_result import CognitiveGateResult


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
    confirmation_request: ConfirmationRequest | None = None
    confirmation_result: ConfirmationResult | None = None

    action_decision: ActionDecision | None = None
    executable_intent: ExecutableIntent | None = None
    conflict: Any | None = None
    # Observability
    predictive: Any | None = None
    stability: Any | None = None
    symbolic: Any | None = None
    system_tension: Any | None = None
    quadratic_lyapunov: Any | None = None
    quadratic_comparability: Any | None = None
    theoretical_regime: Any | None = None
    fast_dynamics: Any | None = None
    perturbation: Any | None = None

    conversation: Any | None = None
    governance: Any | None = None
    pending_actions: Any | None = None
    events: Any | None = None
    coherence_policy: Any | None = None
    memory_influence: dict[str, Any] | None = None
