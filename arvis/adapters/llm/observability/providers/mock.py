# arvis/adapters/llm/observation/providers/mock.py

from typing import Any

from arvis.adapters.llm.observability.observation import LLMObservation

from .base import BaseObservationProvider


class MockObservationProvider(BaseObservationProvider):
    def observe(self, response: Any) -> LLMObservation:
        content = getattr(response, "content", "")

        return LLMObservation(
            entropy_mean=0.5,
            confidence_mean=1.0,
            logprob_variance=0.1,
            output_length=len(content),
            latency_ms=0,
        )
