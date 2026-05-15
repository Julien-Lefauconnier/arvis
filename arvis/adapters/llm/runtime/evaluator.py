# arvis/adapters/llm/runtime/evaluator.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.adapters.llm.observability.observation import LLMObservation


@dataclass(frozen=True)
class EvaluationDecision:
    accept: bool
    retry: bool
    fallback: bool
    require_confirmation: bool


class LLMResponseEvaluator:
    """
    Deterministic evaluation of LLM observation signals.
    """

    def evaluate(self, obs: LLMObservation | None) -> EvaluationDecision:
        if obs is None:
            return EvaluationDecision(True, False, False, False)

        entropy = obs.entropy_mean or 0.0
        confidence = obs.confidence_mean or 0.0
        variance = obs.logprob_variance or 0.0

        # High uncertainty → retry
        if entropy > 1.5 or variance > 0.2:
            return EvaluationDecision(
                accept=False,
                retry=True,
                fallback=False,
                require_confirmation=True,
            )

        # Low confidence → fallback
        if confidence < 0.3:
            return EvaluationDecision(
                accept=False,
                retry=False,
                fallback=True,
                require_confirmation=True,
            )

        # Accept
        return EvaluationDecision(
            accept=True,
            retry=False,
            fallback=False,
            require_confirmation=False,
        )
