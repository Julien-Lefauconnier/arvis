# arvis/kernel/projection/pi_impl.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.observability.observation import LLMObservation
from arvis.math.projection.projection_view import ProjectionView

from .llm_projection_mapper import LLMProjectionMapper
from .pi_types import (
    PiState,
    QState,
    WState,
    XState,
    ZControlState,
    ZDecisionState,
    ZDynamicState,
    ZGateState,
    ZState,
)
from .projected_state import ProjectedState

Number = int | float


class PiImpl:
    """
    Runtime implementation of Π_impl.

    Responsibilities:
    - read canonical runtime signals from pipeline context
    - normalize them into a deterministic projected state
    - remain conservative and fail-soft
    """

    def __init__(self) -> None:
        self._llm_mapper = LLMProjectionMapper()

    def project(self, ctx: Any) -> ProjectedState:
        state_signals: dict[str, float] = {}
        risk_signals: dict[str, float] = {}
        control_signals: dict[str, float] = {}
        trace_features: dict[str, float] = {}

        system_tension = getattr(ctx, "system_tension", None)
        state_signals["system_tension"] = self._coerce(system_tension, 0.0)

        conflict_pressure = getattr(ctx, "conflict_pressure", None)
        risk_signals["conflict_pressure"] = self._coerce(conflict_pressure, 0.0)

        coherence_score = getattr(ctx, "coherence_score", None)
        if isinstance(coherence_score, (int, float)):
            state_signals["coherence_score"] = float(coherence_score)

        control_signal = getattr(ctx, "control_signal", None)
        if isinstance(control_signal, (int, float)):
            control_signals["control_signal"] = float(control_signal)

        adaptive_kappa = getattr(ctx, "adaptive_kappa_eff", None)
        if isinstance(adaptive_kappa, (int, float)):
            trace_features["adaptive_kappa_eff"] = float(adaptive_kappa)

        metadata = {
            "source": "PiImpl",
            "has_observability_snapshot": getattr(ctx, "predictive_snapshot", None)
            is not None,
        }

        extra = getattr(ctx, "extra", None)
        if isinstance(extra, dict):
            llm_obs_raw = extra.get("llm_observation")
            llm_eval_raw = extra.get("llm_evaluation")

            llm_obs = self._safe_to_dict(llm_obs_raw)
            llm_eval = self._safe_to_dict(llm_eval_raw)
        else:
            llm_obs_raw = None
            llm_eval_raw = None
            llm_obs = None
            llm_eval = None

        self._llm_mapper.inject(
            llm_obs,
            llm_eval=llm_eval,
            state_signals=state_signals,
            risk_signals=risk_signals,
            trace_features=trace_features,
        )

        return ProjectedState(
            state_signals=state_signals,
            risk_signals=risk_signals,
            control_signals=control_signals,
            trace_features=trace_features,
            metadata=metadata,
            llm_observation=(
                llm_obs_raw if isinstance(llm_obs_raw, LLMObservation) else None
            ),
        )

    def project_previous(
        self,
        ctx: Any,
    ) -> ProjectionView | None:
        """
        Return the previous flat projection view when available.
        """
        previous = getattr(ctx, "projection_view", None)

        if isinstance(previous, ProjectionView):
            return previous
        return None

    def _coerce(self, value: Any, default: Number = 0.0) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return float(default)

    # =========================================
    # STRUCTURED Π
    # =========================================

    def project_structured(self, ctx: Any) -> PiState:
        ir_state = getattr(ctx, "ir_state", None)
        ir_decision = getattr(ctx, "ir_decision", None)
        ir_gate = getattr(ctx, "ir_gate", None)

        # =========================
        # X STATE
        # =========================

        coherence = self._coerce(getattr(ctx, "coherence_score", None), 0.5)
        tension = self._coerce(getattr(ctx, "system_tension", None), 0.0)
        drift = self._coerce(getattr(ctx, "drift_score", None), 0.0)

        conflict_pressure = self._coerce(getattr(ctx, "collapse_risk", None), 0.0)

        uncertainty = self._coerce(getattr(ctx, "uncertainty", None), 0.0)

        extra = getattr(ctx, "extra", None)
        llm_obs = None
        llm_eval = None

        base_commitment = 0.5

        if isinstance(extra, dict):
            llm_obs = self._safe_to_dict(extra.get("llm_observation"))
            llm_eval = self._safe_to_dict(extra.get("llm_evaluation"))

        if isinstance(llm_obs, dict):
            entropy = llm_obs.get("entropy_mean")
            variance = llm_obs.get("logprob_variance")
            confidence = llm_obs.get("confidence_mean")

            if (
                isinstance(entropy, (int, float))
                and isinstance(variance, (int, float))
                and isinstance(confidence, (int, float))
            ):
                entropy_f = float(entropy)
                variance_f = float(variance)
                confidence_f = float(confidence)

                entropy_n = min(max(entropy_f, 0.0), 1.0)
                variance_n = min(max(variance_f, 0.0), 1.0)
                confidence_n = min(max(confidence_f, 0.0), 1.0)

                # IMPORTANT: preserve monotonicity (test expects >= entropy)
                uncertainty = max(uncertainty, entropy_n, variance_n)

                # affects commitment (soft scaling)
                base_commitment *= 0.5 + 0.5 * confidence_n

        if isinstance(llm_eval, dict):
            eval_uncertainty = llm_eval.get("uncertainty")
            eval_risk = llm_eval.get("risk")

            if isinstance(eval_uncertainty, (int, float)):
                uncertainty = max(uncertainty, float(eval_uncertainty))

            if isinstance(eval_risk, (int, float)):
                uncertainty = max(uncertainty, float(eval_risk))

        if isinstance(llm_eval, dict):
            confidence = llm_eval.get("confidence")
            if isinstance(confidence, (int, float)):
                base_commitment = max(
                    base_commitment,
                    min(max(float(confidence), 0.0), 1.0),
                )
        elif isinstance(llm_obs, dict):
            confidence = llm_obs.get("confidence_mean")
            if isinstance(confidence, (int, float)):
                base_commitment = max(
                    base_commitment,
                    min(max(float(confidence), 0.0), 1.0),
                )

        if ir_decision:
            base_commitment = max(
                base_commitment,
                1.0 if ir_decision.decision_kind else 0.3,
            )

        decision_commitment = min(max(base_commitment, 0.0), 1.0)

        uncertainty = min(max(uncertainty, 0.0), 1.5)

        x = XState(
            cognitive_load=tension,
            coherence_score=coherence,
            conflict_pressure=conflict_pressure,
            uncertainty_mass=uncertainty,
            decision_commitment=decision_commitment,
            memory_activation=0.5,
            symbolic_stability=max(0.0, 1.0 - drift),
            retrieval_salience=0.5,
        )

        # =========================
        # Z STATE
        # =========================

        # decision
        decision_kind = None
        if ir_decision:
            decision_kind = ir_decision.decision_kind

        confidence = max(0.0, min(1.0, 1.0 - uncertainty))

        z_decision = ZDecisionState(
            decision_kind=decision_kind,
            actionability_score=decision_commitment,
            confidence_score=confidence,
        )

        # -----------------------------------------
        # Gate fallback logic (Π must be self-sufficient)
        # -----------------------------------------
        if ir_gate and getattr(ir_gate, "verdict", None):
            verdict = str(getattr(ir_gate.verdict, "value", ir_gate.verdict)).lower()
        else:
            # fallback based on uncertainty & tension
            if uncertainty > 0.8:
                verdict = "require_confirmation"
            elif uncertainty < 0.7:
                verdict = "allow"
            else:
                verdict = "require_confirmation"

            # LLM tightening
            if isinstance(llm_obs, dict):
                var = llm_obs.get("logprob_variance")
                if isinstance(var, (int, float)) and var > 1.2:
                    verdict = "require_confirmation"

            # LLM-aware tightening
            if isinstance(llm_obs, dict):
                conf = llm_obs.get("confidence_mean")
                if isinstance(conf, (int, float)) and conf < 0.3:
                    verdict = "require_confirmation"

        safety_margin = self._coerce(
            getattr(ctx, "projection_margin", getattr(ctx, "m_t", None)), 0.0
        )

        z_gate = ZGateState(
            verdict=verdict,
            safety_margin=safety_margin,
            veto_intensity=1.0 - safety_margin,
            confirmation_required=(verdict == "require_confirmation"),
        )

        # control
        epsilon = self._coerce(
            getattr(ir_state, "epsilon", None) if ir_state else None, 0.1
        )

        z_control = ZControlState(
            control_mode="exploit" if epsilon < 0.2 else "explore",
            epsilon=epsilon,
            beta=1.0,
            exploration_pressure=epsilon,
        )

        # dynamics
        regime = getattr(ctx, "regime", None)

        delta_w = self._coerce(getattr(ctx, "delta_w", None), 0.0)

        z_dyn = ZDynamicState(
            regime=regime,
            temporal_pressure=tension,
            recent_delta_norm=abs(delta_w),
            runtime_instability=drift,
        )

        z = ZState(
            decision=z_decision,
            gate=z_gate,
            control=z_control,
            dynamics=z_dyn,
        )

        # =========================
        # Q STATE
        # =========================

        q = QState(
            regime_mode=regime,
            gate_mode=verdict,
            conversation_mode=None,
            execution_mode=None,
            switching_safe=bool(getattr(ctx, "switching_safe", True)),
        )

        # =========================
        # W STATE
        # =========================

        llm_pressure = 0.0
        llm_risk_pressure = 0.0

        if isinstance(llm_obs, dict):
            entropy = llm_obs.get("entropy_mean")
            variance = llm_obs.get("logprob_variance")
            confidence = llm_obs.get("confidence_mean")

            if isinstance(variance, (int, float)):
                llm_pressure = max(
                    llm_pressure,
                    min(max(float(variance), 0.0), 1.0),
                )

            if isinstance(entropy, (int, float)):
                llm_pressure = max(
                    llm_pressure,
                    min(max(float(entropy), 0.0), 1.0),
                )

            if isinstance(confidence, (int, float)):
                llm_risk_pressure = max(
                    llm_risk_pressure,
                    1.0 - min(max(float(confidence), 0.0), 1.0),
                )

        if isinstance(llm_eval, dict):
            eval_risk = llm_eval.get("risk")
            eval_uncertainty = llm_eval.get("uncertainty")

            if isinstance(eval_risk, (int, float)):
                llm_risk_pressure = max(
                    llm_risk_pressure,
                    min(max(float(eval_risk), 0.0), 1.0),
                )

            if isinstance(eval_uncertainty, (int, float)):
                llm_pressure = max(
                    llm_pressure,
                    min(max(float(eval_uncertainty), 0.0), 1.0),
                )

        w = WState(
            uncertainty_pressure=max(uncertainty, llm_risk_pressure),
            ambiguity_pressure=min(1.5, uncertainty + llm_pressure),
            observation_gap=max(uncertainty, llm_risk_pressure),
            external_disturbance=min(1.5, drift + llm_pressure + llm_risk_pressure),
            projection_residual=1.0 - safety_margin,
            llm_risk_pressure=llm_risk_pressure,
        )

        return PiState(x=x, z=z, q=q, w=w)

    def _safe_to_dict(self, value: Any) -> dict[str, float] | None:
        if isinstance(value, dict):
            return value  # assume already sanitized

        if isinstance(value, LLMObservation):
            return value.to_dict()

        # support LLMEvaluation
        if hasattr(value, "to_dict"):
            candidate = value.to_dict()
            if isinstance(candidate, dict):
                return candidate

        return None
