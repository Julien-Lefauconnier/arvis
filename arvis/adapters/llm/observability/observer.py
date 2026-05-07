# arvis/adapters/llm/observability/observer.py

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from arvis.adapters.llm.contracts.response import LLMResponse

from .math_utils import compute_confidence, compute_entropy, compute_variance
from .observation import LLMObservation


class ObservationProvider(Protocol):
    def observe(self, response: LLMResponse) -> LLMObservation: ...


class LLMObserver:
    """
    Extracts observability signals from LLMResponse metadata.
    """

    def __init__(self, provider: ObservationProvider | None = None) -> None:
        self._provider = provider

    def observe(self, response: LLMResponse) -> LLMObservation | None:
        if self._provider is not None:
            return self._provider.observe(response)

        metadata = response.metadata or {}

        logprobs = metadata.get("logprobs")

        if isinstance(logprobs, Sequence) and not isinstance(logprobs, (str, bytes)):
            entropy = compute_entropy(logprobs)
            variance = compute_variance(logprobs)
            confidence = compute_confidence(logprobs)
        else:
            entropy = None
            variance = None
            confidence = None

        token_count = metadata.get("token_count")
        latency_ms = metadata.get("latency_ms")

        return LLMObservation(
            entropy_mean=entropy,
            confidence_mean=confidence,
            logprob_variance=variance,
            output_length=token_count if isinstance(token_count, int) else None,
            latency_ms=latency_ms,
        )
