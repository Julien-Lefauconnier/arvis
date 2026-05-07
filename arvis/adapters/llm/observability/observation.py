# arvis/adapters/llm/observability/observation.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LLMObservation:
    entropy_mean: float | None = None
    confidence_mean: float | None = None
    logprob_variance: float | None = None
    output_length: int | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, float]:
        out: dict[str, float] = {}

        if self.entropy_mean is not None:
            out["entropy_mean"] = float(self.entropy_mean)

        if self.confidence_mean is not None:
            out["confidence_mean"] = float(self.confidence_mean)

        if self.logprob_variance is not None:
            out["logprob_variance"] = float(self.logprob_variance)

        if self.output_length is not None:
            out["output_length"] = float(self.output_length)

        if self.latency_ms is not None:
            out["latency_ms"] = float(self.latency_ms)

        return out
