# arvis/adapters/llm/epistemic/state.py

from dataclasses import dataclass

from arvis.adapters.llm.observability.observation import LLMObservation


@dataclass(frozen=True, slots=True)
class LLMEpistemicState:
    # Raw
    entropy: float
    variance: float
    confidence: float

    # Derived
    uncertainty: float
    risk: float
    instability: float

    @staticmethod
    def from_observation(obs: "LLMObservation") -> "LLMEpistemicState":
        entropy = float(obs.entropy_mean or 0.0)
        variance = float(obs.logprob_variance or 0.0)
        confidence = float(obs.confidence_mean or 0.0)

        entropy_n = min(max(entropy, 0.0), 1.0)
        variance_n = min(max(variance, 0.0), 1.0)
        confidence_n = min(max(confidence, 0.0), 1.0)

        uncertainty = max(entropy_n, variance_n)
        instability = entropy_n * variance_n
        risk = max(uncertainty, 1.0 - confidence_n)

        return LLMEpistemicState(
            entropy=entropy_n,
            variance=variance_n,
            confidence=confidence_n,
            uncertainty=uncertainty,
            risk=risk,
            instability=instability,
        )
