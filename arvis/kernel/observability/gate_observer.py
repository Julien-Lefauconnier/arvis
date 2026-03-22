# arvis/kernel/observability/gate_observer.py

from __future__ import annotations
from typing import Any, Optional, Dict


class GateObserver:
    """
    Pure observability layer for GateStage.

    IMPORTANT:
    - No decision logic
    - No mutation of verdict
    - Only builds ctx.extra projections
    """

    def build(
        self,
        ctx: Any,
        *,
        pre_verdict: Any,
        final_verdict: Any,
        delta_w: Optional[float],
        w_prev: Optional[float],
        w_current: Optional[float],
        adaptive_metrics: Optional[Dict[str, Any]],
        switching_safe: bool,
        global_safe: bool,
        envelope: Any,
        confidence_inputs: Any,
        system_confidence: float,
        switching_metrics: Dict[str, Any],
        stability_certificate: Dict[str, Any],
        hard_block: bool,
        hard_reason: Optional[str],
        w_ratio: Optional[float],
        recovery_detected: bool,
        recovery_magnitude: Optional[float],
    ) -> None:

        # -----------------------------------------
        # fusion_trace
        # -----------------------------------------
        ctx.extra["system_confidence"] = float(system_confidence)
        ctx.extra.setdefault("confidence_flags", [])
        ctx.extra["fusion_trace"] = {
            "pre_verdict": str(pre_verdict),
            "final_verdict": str(final_verdict),
            "delta_w": delta_w,

            "global_safe": bool(global_safe),
            "switching_safe": bool(switching_safe),
            "confidence_inputs": {
                "delta_w": confidence_inputs.delta_w,
                "global_safe": confidence_inputs.global_safe,
                "switching_safe": confidence_inputs.switching_safe,
                "has_history": confidence_inputs.has_history,
                "has_observability": confidence_inputs.has_observability,
                "collapse_risk": confidence_inputs.collapse_risk,
            },
            "system_confidence": float(system_confidence),
            "reasons": list(ctx.extra.get("fusion_reasons", [])),
        }

        # -----------------------------------------
        # theoretical_trace
        # -----------------------------------------
        ctx.extra["stability_certificate"] = dict(stability_certificate or {})
        ctx.extra["theoretical_trace"] = {
            "lyapunov": {
                "w_prev": float(w_prev) if w_prev is not None else None,
                "w_current": float(w_current) if w_current is not None else None,
                "delta_w": float(delta_w) if delta_w is not None else None,
            },
            "adaptive": ctx.extra.get("adaptive_trace"),
            "switching": dict(switching_metrics or {}),
            "global": {
                "safe": bool(global_safe),
                "history_len": len(ctx.delta_w_history),
            },
            "envelope": {
                "hard_block": envelope.hard_block,
                "reason": envelope.hard_reason,
                "w_bound_ratio": envelope.w_bound_ratio,
            },
            "certificate": dict(stability_certificate or {}),
            "decision_flow": {
                "pre_verdict": str(pre_verdict),
                "final_verdict": str(final_verdict),
            },
        }

        # canonical projection
        ctx.extra["switching_metrics"] = dict(switching_metrics or {})

        # -----------------------------------------
        # adaptive_trace
        # -----------------------------------------
        if adaptive_metrics:
            ctx.extra["adaptive_trace"] = {
                "kappa_eff": adaptive_metrics.get("kappa_eff"),
                "margin": adaptive_metrics.get("margin"),
                "regime": adaptive_metrics.get("regime"),
                "available": adaptive_metrics.get("available"),
            }
        else:
            ctx.extra["adaptive_trace"] = {"available": False}

        # -----------------------------------------
        # disturbance_signals
        # -----------------------------------------
        disturbance: Dict[str, Optional[float | bool]] = {
            "projection_disturbance": None,
            "switching_disturbance": None,
            "adaptive_warning": False,
            "global_instability": bool(ctx.extra.get("global_instability", False)),
        }

        try:
            if w_current is not None and delta_w is not None:
                denom = max(abs(w_current), 1e-6)
                disturbance["projection_disturbance"] = float(abs(delta_w) / denom)
        except Exception:
            pass

        try:
            if not switching_safe:
                disturbance["switching_disturbance"] = True
        except Exception:
            pass

        if adaptive_metrics and adaptive_metrics.get("margin") is not None:
            if adaptive_metrics["margin"] > -0.02:
                disturbance["adaptive_warning"] = True

        ctx.extra["disturbance_signals"] = disturbance

        # -----------------------------------------
        # theoretical_signature
        # -----------------------------------------
        ctx.extra["theoretical_signature"] = {
            "model": "ARVIS_GATE_V1",
            "components": [
                "lyapunov",
                "adaptive",
                "switching",
                "global_guard",
                "fusion",
            ],
        }

        # -----------------------------------------
        # hard_block_log (observability only)
        # -----------------------------------------
        if hard_block:
            ctx.extra["hard_block_log"] = {
                "reasons": hard_reason,
                "delta_w": delta_w,
                "w_ratio": w_ratio,
            }

        # -----------------------------------------
        # recovery signals (observability only)
        # -----------------------------------------
        if recovery_detected:
            ctx.extra["recovery_detected"] = True
            ctx.extra["recovery_magnitude"] = recovery_magnitude