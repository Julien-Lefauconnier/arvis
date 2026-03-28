# arvis/kernel/projection/pi_impl.py

from __future__ import annotations

from typing import Any, Dict, Optional

from .projected_state import ProjectedState


class PiImpl:
    """
    Runtime implementation of Π_impl.

    Responsibilities:
    - read canonical runtime signals from pipeline context
    - normalize them into a deterministic projected state
    - remain conservative and fail-soft
    """

    def project(self, ctx: Any) -> ProjectedState:
        state_signals: Dict[str, float] = {}
        risk_signals: Dict[str, float] = {}
        control_signals: Dict[str, float] = {}
        trace_features: Dict[str, float] = {}

        def _coerce(value: Any, default: float = 0.0) -> float:
            if isinstance(value, (int, float)):
                return float(value)
            return float(default)

        system_tension = getattr(ctx, "system_tension", None)
        state_signals["system_tension"] = _coerce(system_tension, 0.0)

        conflict_pressure = getattr(ctx, "conflict_pressure", None)
        if isinstance(conflict_pressure, (int, float)):
            risk_signals["conflict_pressure"] = float(conflict_pressure)

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
            "has_observability_snapshot": getattr(ctx, "predictive_snapshot", None) is not None,
        }

        return ProjectedState(
            state_signals=state_signals,
            risk_signals=risk_signals,
            control_signals=control_signals,
            trace_features=trace_features,
            metadata=metadata,
        )

    def project_previous(self, ctx: Any) -> Optional[Dict[str, float]]:
        """
        Return the previous flat projection view when available.
        """
        previous = getattr(ctx, "projection_view", None)
        if isinstance(previous, dict):
            out: Dict[str, float] = {}
            for key, value in previous.items():
                if isinstance(value, (int, float)):
                    out[str(key)] = float(value)
            return out
        return None