# arvis/adapters/llm/observation/providers/openai.py

from typing import Any

from arvis.adapters.llm.observability.math_utils import (
    compute_entropy,
    compute_variance,
)
from arvis.adapters.llm.observability.observation import LLMObservation

from .base import BaseObservationProvider


class OpenAIObservationProvider(BaseObservationProvider):
    def observe(self, response: Any) -> LLMObservation:
        tokens = response.logprobs.tokens if hasattr(response, "logprobs") else []

        logprobs = [t.logprob for t in tokens] if tokens else []

        entropy = compute_entropy(logprobs) if logprobs else None
        variance = compute_variance(logprobs) if logprobs else None

        return LLMObservation(
            entropy_mean=entropy,
            logprob_variance=variance,
            output_length=len(tokens),
        )
