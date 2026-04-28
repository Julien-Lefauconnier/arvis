# arvis/kernel/observability/gate_observer.py

from __future__ import annotations
from typing import Any, Optional, Dict
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot


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
        adaptive_metrics: Optional[AdaptiveSnapshot],
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
        ctx.extra["system_confidence"] = float(system_confidence)
        ctx.extra.setdefault("confidence_flags", [])

        # -----------------------------------------
        # adaptive_trace
        # -----------------------------------------
        if adaptive_metrics:
            adaptive_trace = {
                "kappa_eff": adaptive_metrics.kappa_eff,
                "margin": adaptive_metrics.margin,
                "regime": adaptive_metrics.regime,
                "available": adaptive_metrics.is_available,
            }
        else:
            adaptive_trace = {"available": False}
        ctx.extra["adaptive_trace"] = adaptive_trace
        # -----------------------------------------
        # projection_trace
        # -----------------------------------------
        projection_certificate = getattr(ctx, "projection_certificate", None)
        projection_view = getattr(ctx, "projection_view", None)
        projection_view_raw = getattr(ctx, "projection_view_raw", None)

        projection_trace = {
            "available": projection_certificate is not None,
            "domain_valid": (
                bool(getattr(projection_certificate, "domain_valid", False))
                if projection_certificate is not None
                else None
            ),
            "safe": (
                bool(getattr(projection_certificate, "is_projection_safe", False))
                if projection_certificate is not None
                else None
            ),
            "lyapunov_compatible": (
                bool(
                    getattr(projection_certificate, "lyapunov_compatibility_ok", False)
                )
                if projection_certificate is not None
                else None
            ),
            "margin": (
                float(getattr(projection_certificate, "margin_to_boundary"))
                if projection_certificate is not None
                and getattr(projection_certificate, "margin_to_boundary", None)
                is not None
                else None
            ),
            "certification_level": (
                str(
                    getattr(
                        getattr(projection_certificate, "certification_level", None),
                        "value",
                        None,
                    )
                )
                if projection_certificate is not None
                else None
            ),
            "view": dict(projection_view)
            if isinstance(projection_view, dict)
            else None,
            "raw_view": dict(projection_view_raw)
            if isinstance(projection_view_raw, dict)
            else None,
        }

        projection_summary = {
            "available": projection_trace["available"],
            "domain_valid": projection_trace["domain_valid"],
            "safe": projection_trace["safe"],
            "lyapunov_compatible": projection_trace["lyapunov_compatible"],
            "margin": projection_trace["margin"],
            "certification_level": projection_trace["certification_level"],
        }

        # -----------------------------------------
        # fusion_trace
        # -----------------------------------------
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
            "projection": projection_summary,
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
            "adaptive": adaptive_trace,
            "switching": dict(switching_metrics or {}),
            "global": {
                "safe": bool(global_safe),
                "history_len": len(ctx.delta_w_history),
            },
            "projection": {
                **projection_summary,
                "view": projection_trace["view"],
                "raw_view": projection_trace["raw_view"],
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
        ctx.extra["projection_trace"] = projection_trace

        # -----------------------------------------
        # disturbance_signals
        # -----------------------------------------
        disturbance: Dict[str, Optional[float | bool]] = {
            "projection_disturbance": None,
            "switching_disturbance": None,
            "adaptive_warning": False,
            "global_instability": bool(ctx.extra.get("global_instability", False)),
            "projection_lyapunov_incompatible": (
                ctx.extra.get("projection_lyapunov_compatible") is False
                or projection_trace.get("lyapunov_compatible") is False
            ),
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

        if adaptive_metrics and adaptive_metrics.margin is not None:
            if adaptive_metrics.margin < 0:
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
