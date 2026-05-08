# arvis/adapters/llm/observability/risk_signal.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LLMRiskSignal:
    """
    Provider-agnostic LLM runtime risk signal.

    This object is intentionally normalized and kernel-safe:
    no provider-specific payload, no raw text, no private content.
    """

    entropy_pressure: float = 0.0
    confidence_risk: float = 0.0
    variance_pressure: float = 0.0
    evaluation_risk: float = 0.0
    uncertainty_pressure: float = 0.0

    @property
    def risk_pressure(self) -> float:
        return max(
            self.entropy_pressure,
            self.confidence_risk,
            self.variance_pressure,
            self.evaluation_risk,
            self.uncertainty_pressure,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "entropy_pressure": self.entropy_pressure,
            "confidence_risk": self.confidence_risk,
            "variance_pressure": self.variance_pressure,
            "evaluation_risk": self.evaluation_risk,
            "uncertainty_pressure": self.uncertainty_pressure,
            "risk_pressure": self.risk_pressure,
        }
