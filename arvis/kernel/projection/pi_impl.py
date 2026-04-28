# arvis/kernel/projection/pi_impl.py

from __future__ import annotations

from typing import Any

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

        return ProjectedState(
            state_signals=state_signals,
            risk_signals=risk_signals,
            control_signals=control_signals,
            trace_features=trace_features,
            metadata=metadata,
        )

    def project_previous(self, ctx: Any) -> dict[str, float] | None:
        """
        Return the previous flat projection view when available.
        """
        previous = getattr(ctx, "projection_view", None)
        if isinstance(previous, dict):
            out: dict[str, float] = {}
            for key, value in previous.items():
                if isinstance(value, (int, float)):
                    out[str(key)] = float(value)
            return out
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

        decision_commitment = 0.5
        if ir_decision:
            decision_commitment = 1.0 if ir_decision.decision_kind else 0.3

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

        confidence = 1.0 - uncertainty

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

        w = WState(
            uncertainty_pressure=uncertainty,
            ambiguity_pressure=uncertainty,
            observation_gap=uncertainty,
            external_disturbance=drift,
            projection_residual=1.0 - safety_margin,
        )

        return PiState(x=x, z=z, q=q, w=w)
