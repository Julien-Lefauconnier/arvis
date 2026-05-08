# arvis/adapters/llm/observability/evaluation.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LLMEvaluation:
    confidence: float | None = None
    uncertainty: float | None = None
    risk: float | None = None
    variance: float | None = None

    def to_dict(self) -> dict[str, float]:
        out: dict[str, float] = {}

        if self.confidence is not None:
            out["confidence"] = float(self.confidence)

        if self.uncertainty is not None:
            out["uncertainty"] = float(self.uncertainty)

        if self.risk is not None:
            out["risk"] = float(self.risk)

        if self.variance is not None:
            out["variance"] = float(self.variance)

        return out
