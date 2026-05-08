# arvis/kernel/projection/llm_projection_mapper.py

from __future__ import annotations

from typing import Any


class LLMProjectionMapper:
    def inject(
        self,
        llm_obs: dict[str, Any] | None,
        llm_eval: dict[str, Any] | None = None,
        *,
        state_signals: dict[str, float],
        risk_signals: dict[str, float],
        trace_features: dict[str, float],
    ) -> None:
        # =========================
        # OBSERVATION NORMALIZATION
        # =========================
        if llm_obs is not None and hasattr(llm_obs, "to_dict"):
            candidate = llm_obs.to_dict()
            if isinstance(candidate, dict):
                llm_obs = candidate
            else:
                return

        if not isinstance(llm_obs, dict):
            return

        obs: dict[str, Any] = llm_obs

        # =========================
        # EVALUATION NORMALIZATION
        # =========================
        if llm_eval is not None and hasattr(llm_eval, "to_dict"):
            candidate = llm_eval.to_dict()
            if isinstance(candidate, dict):
                llm_eval = candidate
            else:
                llm_eval = None

        if not isinstance(llm_eval, dict):
            llm_eval = None

        entropy = obs.get("entropy_mean")
        confidence = obs.get("confidence_mean")
        variance = obs.get("logprob_variance")

        if not (
            isinstance(entropy, (int, float))
            and isinstance(confidence, (int, float))
            and isinstance(variance, (int, float))
        ):
            return

        entropy_f = float(entropy)
        confidence_f = float(confidence)
        variance_f = float(variance)

        # =========================
        # NORMALIZATION (bounded)
        # =========================

        entropy_n = min(max(entropy_f, 0.0), 1.0)
        variance_n = min(max(variance_f, 0.0), 1.0)
        confidence_n = min(max(confidence_f, 0.0), 1.0)

        # =========================
        # DERIVED SIGNALS
        # =========================

        uncertainty_mass = max(entropy_n, variance_n)
        instability = entropy_n * variance_n

        # =========================
        # INJECTION
        # =========================

        state_signals["llm_confidence"] = confidence_n

        # --- BACKWARD COMPAT (tests + existing API) ---
        # (observation-driven signals)
        risk_signals["llm_uncertainty"] = uncertainty_mass
        risk_signals["llm_variance"] = variance_n

        risk_signals["llm_uncertainty_mass"] = uncertainty_mass
        risk_signals["llm_instability"] = instability

        trace_features["llm_entropy"] = entropy_n
        trace_features["llm_variance"] = variance_n

        # =========================
        # EVALUATION INJECTION
        # =========================
        if llm_eval is not None:
            eval_conf = llm_eval.get("confidence")
            eval_uncertainty = llm_eval.get("uncertainty")
            eval_risk = llm_eval.get("risk")
            eval_variance = llm_eval.get("variance")

            if isinstance(eval_conf, (int, float)):
                state_signals["llm_eval_confidence"] = float(eval_conf)

            if isinstance(eval_uncertainty, (int, float)):
                risk_signals["llm_eval_uncertainty"] = float(eval_uncertainty)

            if isinstance(eval_risk, (int, float)):
                risk_signals["llm_eval_risk"] = float(eval_risk)

            if isinstance(eval_variance, (int, float)):
                trace_features["llm_eval_variance"] = float(eval_variance)

        # optional signals
        output_len = obs.get("output_length")
        if isinstance(output_len, (int, float)):
            trace_features["llm_output_length"] = float(output_len)

        latency = obs.get("latency_ms")
        if isinstance(latency, (int, float)):
            trace_features["llm_latency"] = float(latency)
