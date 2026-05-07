# arvis/kernel/projection/llm_projection_mapper.py

from __future__ import annotations

from typing import Any


class LLMProjectionMapper:
    def inject(
        self,
        llm_obs: dict[str, Any] | None,
        *,
        state_signals: dict[str, float],
        risk_signals: dict[str, float],
        trace_features: dict[str, float],
    ) -> None:
        if not isinstance(llm_obs, dict):
            return

        entropy = llm_obs.get("entropy_mean")
        confidence = llm_obs.get("confidence_mean")
        variance = llm_obs.get("logprob_variance")
        output_len = llm_obs.get("output_length")
        latency = llm_obs.get("latency_ms")

        if isinstance(entropy, (int, float)):
            trace_features["llm_entropy"] = float(entropy)
            risk_signals["llm_uncertainty"] = float(entropy)

        if isinstance(confidence, (int, float)):
            state_signals["llm_confidence"] = float(confidence)

        if isinstance(variance, (int, float)):
            risk_signals["llm_variance"] = float(variance)

        if isinstance(output_len, (int, float)):
            trace_features["llm_output_length"] = float(output_len)

        if isinstance(latency, (int, float)):
            trace_features["llm_latency"] = float(latency)
            risk_signals["llm_latency"] = float(latency)
