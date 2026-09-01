# arvis/kernel/observability/gate_observer.py

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot

if TYPE_CHECKING:
    from arvis.kernel.pipeline.stages.gate.models import (
        CompositeMetrics,
        GateDecisionResult,
        StabilityAssessment,
    )


@dataclass(frozen=True, slots=True)
class GateObservation:
    """Everything the gate observer projects into ctx.extra, as one
    typed value (campaign STRUCT, LOT S5: build() took twenty keyword
    parameters, all derived from three gate result objects)."""

    pre_verdict: Any
    final_verdict: Any
    delta_w: float | None
    w_prev: float | None
    w_current: float | None
    adaptive_metrics: AdaptiveSnapshot | None
    switching_safe: bool
    global_safe: bool
    envelope: Any
    confidence_inputs: Any
    system_confidence: float
    switching_metrics: dict[str, Any]
    stability_certificate: dict[str, Any]
    hard_block: bool
    hard_reason: str | None
    w_ratio: float | None
    recovery_detected: bool
    recovery_magnitude: float | None

    @classmethod
    def from_gate_results(
        cls,
        composite: CompositeMetrics,
        assessment: StabilityAssessment,
        decision: GateDecisionResult,
    ) -> GateObservation:
        """Derive the observation from the gate's three result objects
        (the single production call path)."""
        return cls(
            pre_verdict=decision.pre_verdict,
            final_verdict=decision.verdict,
            delta_w=composite.delta_w,
            w_prev=composite.w_prev,
            w_current=composite.w_current,
            adaptive_metrics=assessment.adaptive_metrics,
            switching_safe=assessment.switching_safe,
            global_safe=assessment.global_safe,
            envelope=assessment.envelope,
            confidence_inputs=assessment.confidence_inputs,
            system_confidence=assessment.system_confidence,
            switching_metrics=assessment.switching_metrics,
            stability_certificate=decision.stability_certificate,
            hard_block=assessment.envelope.hard_block,
            hard_reason=assessment.envelope.hard_reason,
            w_ratio=assessment.w_ratio,
            recovery_detected=assessment.recovery_detected,
            recovery_magnitude=(
                abs(composite.delta_w)
                if (composite.delta_w is not None and assessment.recovery_detected)
                else None
            ),
        )


class GateObserver:
    """
    Pure observability layer for GateStage.

    IMPORTANT:
    - No decision logic
    - No mutation of verdict
    - Only builds ctx.extra projections
    """

    def build(self, ctx: Any, observation: GateObservation) -> None:
        pre_verdict = observation.pre_verdict
        final_verdict = observation.final_verdict
        delta_w = observation.delta_w
        w_prev = observation.w_prev
        w_current = observation.w_current
        adaptive_metrics = observation.adaptive_metrics
        switching_safe = observation.switching_safe
        global_safe = observation.global_safe
        envelope = observation.envelope
        confidence_inputs = observation.confidence_inputs
        system_confidence = observation.system_confidence
        switching_metrics = observation.switching_metrics
        stability_certificate = observation.stability_certificate

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
        projection_ctx = getattr(ctx, "projection", None)

        if projection_ctx is not None:
            projection_certificate = getattr(
                projection_ctx,
                "certificate",
                None,
            )
            projection_view = getattr(
                projection_ctx,
                "view",
                None,
            )
            projection_view_raw = getattr(
                projection_ctx,
                "view_raw",
                None,
            )
        else:
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
                float(projection_certificate.margin_to_boundary)
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
            "view": (
                (
                    projection_view.to_dict()
                    if projection_view is not None
                    and hasattr(projection_view, "to_dict")
                    else (
                        MappingProxyType(dict(projection_view))
                        if projection_view is not None
                        else None
                    )
                )
                if projection_view is not None
                else None
            ),
            "raw_view": (
                MappingProxyType(dict(projection_view_raw))
                if projection_view_raw is not None
                else None
            ),
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
        ctx.extra["stability_certificate"] = MappingProxyType(
            dict(stability_certificate or {})
        )
        ctx.extra["theoretical_trace"] = {
            "lyapunov": {
                "w_prev": float(w_prev) if w_prev is not None else None,
                "w_current": float(w_current) if w_current is not None else None,
                "delta_w": float(delta_w) if delta_w is not None else None,
            },
            "adaptive": adaptive_trace,
            "switching": MappingProxyType(dict(switching_metrics or {})),
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
            "certificate": MappingProxyType(dict(stability_certificate or {})),
            "decision_flow": {
                "pre_verdict": str(pre_verdict),
                "final_verdict": str(final_verdict),
            },
        }

        # canonical projection
        ctx.extra["switching_metrics"] = MappingProxyType(dict(switching_metrics or {}))
        ctx.extra["projection_trace"] = projection_trace

        # -----------------------------------------
        # disturbance_signals
        # -----------------------------------------
        disturbance: dict[str, float | bool | None] = {
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
        except (TypeError, ValueError, OverflowError):
            pass

        try:
            if not switching_safe:
                disturbance["switching_disturbance"] = True
        except Exception:  # arvis-broad: fail-soft gate observer
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
        if observation.hard_block:
            ctx.extra["hard_block_log"] = {
                "reasons": observation.hard_reason,
                "delta_w": delta_w,
                "w_ratio": observation.w_ratio,
            }

        # -----------------------------------------
        # recovery signals (observability only)
        # -----------------------------------------
        if observation.recovery_detected:
            ctx.extra["recovery_detected"] = True
            ctx.extra["recovery_magnitude"] = observation.recovery_magnitude
