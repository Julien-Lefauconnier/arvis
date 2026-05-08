# arvis/adapters/llm/observability/risk_mapper.py

from __future__ import annotations

from arvis.adapters.llm.observability.evaluation import (
    LLMEvaluation,
)
from arvis.adapters.llm.observability.observation import (
    LLMObservation,
)
from arvis.adapters.llm.observability.risk_signal import (
    LLMRiskSignal,
)


class LLMRiskSignalMapper:
    """
    Maps raw LLM observability outputs
    into normalized kernel-safe risk signals.
    """

    def build(
        self,
        observation: LLMObservation | None,
        evaluation: LLMEvaluation | None,
    ) -> LLMRiskSignal:
        entropy_pressure = 0.0
        confidence_risk = 0.0
        variance_pressure = 0.0
        evaluation_risk = 0.0
        uncertainty_pressure = 0.0

        if observation is not None:
            entropy_pressure = float(observation.entropy_mean or 0.0)

            confidence_mean = float(observation.confidence_mean or 1.0)

            confidence_risk = max(
                0.0,
                1.0 - confidence_mean,
            )

            variance_pressure = float(observation.logprob_variance or 0.0)

        if evaluation is not None:
            evaluation_risk = float(evaluation.risk or 0.0)

            uncertainty_pressure = float(evaluation.uncertainty or 0.0)

        return LLMRiskSignal(
            entropy_pressure=entropy_pressure,
            confidence_risk=confidence_risk,
            variance_pressure=variance_pressure,
            evaluation_risk=evaluation_risk,
            uncertainty_pressure=uncertainty_pressure,
        )
