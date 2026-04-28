# arvis/api/trace.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DecisionTraceView:
    """
    Public, structured and stable representation of DecisionTrace.
    """

    timestamp: str
    user_id: str

    # Core
    decision: Optional[str]
    intent: Optional[str]

    # Gate
    gate_verdict: Optional[str]

    # Confirmation
    confirmation_required: bool
    confirmation_granted: Optional[bool]

    # Observability
    stability: Optional[Any]
    predictive: Optional[Any]
    symbolic: Optional[Any]
    system_tension: Optional[Any]

    # Meta
    has_conflict: bool
    has_governance: bool
    has_pending_actions: bool

    # -----------------------------------------------------
    # BUILDERS
    # -----------------------------------------------------

    @staticmethod
    def from_trace(trace: Any) -> "DecisionTraceView":
        return DecisionTraceView(
            timestamp=str(getattr(trace, "timestamp", "")),
            user_id=str(getattr(trace, "user_id", "")),
            decision=str(trace.action_decision) if trace.action_decision else None,
            intent=str(trace.executable_intent) if trace.executable_intent else None,
            gate_verdict=(
                str(_safe_attr(getattr(trace, "gate_result", None), "verdict"))
            ),
            confirmation_required=getattr(trace, "confirmation_request", None)
            is not None,
            confirmation_granted=_safe_attr(
                getattr(trace, "confirmation_result", None), "confirmed"
            ),
            stability=trace.stability,
            predictive=trace.predictive,
            symbolic=trace.symbolic,
            system_tension=trace.system_tension,
            has_conflict=trace.conflict is not None,
            has_governance=trace.governance is not None,
            has_pending_actions=trace.pending_actions is not None,
        )

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "decision": self.decision,
            "intent": self.intent,
            "gate": {
                "verdict": self.gate_verdict,
            },
            "confirmation": {
                "required": self.confirmation_required,
                "granted": self.confirmation_granted,
            },
            "observability": {
                "stability": (
                    {
                        "score": getattr(self.stability, "score", None),
                        "risk": getattr(self.stability, "collapse_risk", None),
                        "regime": getattr(self.stability, "verdict", None),
                    }
                    if self.stability
                    else None
                ),
                "predictive": str(self.predictive),
                "symbolic": str(self.symbolic),
                "system_tension": str(self.system_tension),
            },
            "flags": {
                "conflict": self.has_conflict,
                "governance": self.has_governance,
                "pending": self.has_pending_actions,
            },
        }

    def summary(self) -> str:
        return (
            f"[{self.timestamp}] "
            f"Decision={self.decision} | "
            f"Gate={self.gate_verdict} | "
            f"Confirmed={self.confirmation_granted}"
        )


# -----------------------------------------------------
# HELPERS
# -----------------------------------------------------
def _safe_attr(obj: Any, attr: str, default: Any = None) -> Any:
    return getattr(obj, attr, default) if obj is not None else default
