# arvis/kernel/pipeline/stages/gate/adaptive.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.adaptive.adaptive_runtime_observer import AdaptiveRuntimeObserver
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def compute_adaptive_metrics(
    pipeline: Any,
    ctx: Any,
    w_prev: float | None,
    w_current: float | None,
) -> AdaptiveSnapshot | None:
    adaptive_metrics: AdaptiveSnapshot | None = None
    try:
        if (
            w_prev is not None
            and w_current is not None
            and ctx.switching_runtime
            and ctx.switching_params
        ):
            if not hasattr(pipeline, "adaptive_observer"):
                pipeline.adaptive_observer = AdaptiveRuntimeObserver(
                    estimator=pipeline.adaptive_kappa_estimator
                )

            tau_d = float(ctx.switching_runtime.dwell_time())
            J = float(ctx.switching_params.J)

            adaptive_metrics = pipeline.adaptive_observer.update(
                W_prev=w_prev,
                W_next=w_current,
                J=J,
                tau_d=tau_d,
            )
            ctx.adaptive_snapshot = adaptive_metrics
    except Exception:
        adaptive_metrics = None

    if adaptive_metrics is None:
        adaptive_metrics = getattr(ctx, "adaptive_snapshot", None)

    return adaptive_metrics


def apply_kappa_margin_layer(
    ctx: Any,
    pre_verdict: LyapunovVerdict,
    adaptive_metrics: AdaptiveSnapshot | None,
) -> None:
    try:
        if adaptive_metrics is None or adaptive_metrics.margin is None:
            return

        kappa_margin = float(adaptive_metrics.margin)
        ctx.extra["kappa_margin"] = kappa_margin

        if kappa_margin > 0.0:
            kappa_band = "hard"
        elif kappa_margin > -0.02:
            kappa_band = "critical"
        elif kappa_margin > -0.05:
            kappa_band = "warning"
        else:
            kappa_band = "stable"

        ctx.extra["kappa_band"] = kappa_band
        reasons = ctx.extra.setdefault("fusion_reasons", [])

        if kappa_band == "critical":
            if "kappa_margin_critical" not in reasons:
                reasons.append("kappa_margin_critical")
            if pre_verdict == LyapunovVerdict.ALLOW:
                ctx.extra["_kappa_margin_forced_confirmation"] = True
        elif kappa_band == "warning":
            if "kappa_margin_warning" not in reasons:
                reasons.append("kappa_margin_warning")
    except Exception:
        pass


def updated_pre_verdict(
    ctx: Any,
    pre_verdict: LyapunovVerdict,
    adaptive_metrics: AdaptiveSnapshot | None,
) -> LyapunovVerdict:
    if ctx.extra.pop("_kappa_margin_forced_confirmation", False):
        return LyapunovVerdict.REQUIRE_CONFIRMATION
    if (
        adaptive_metrics
        and adaptive_metrics.is_available
        and adaptive_metrics.is_unstable
    ):
        return LyapunovVerdict.ABSTAIN
    return pre_verdict


def apply_final_adaptive_veto(
    ctx: Any,
    verdict: LyapunovVerdict,
    adaptive_metrics: AdaptiveSnapshot | None,
) -> LyapunovVerdict:
    if adaptive_metrics and adaptive_metrics.is_unstable:
        record_verdict_transition(
            ctx,
            stage="final_adaptive_hard_veto",
            before=verdict,
            after=LyapunovVerdict.ABSTAIN,
            reason="adaptive_metrics_unstable",
        )
        verdict = LyapunovVerdict.ABSTAIN
    return verdict


__all__ = [
    "AdaptiveRuntimeObserver",
    "compute_adaptive_metrics",
    "apply_kappa_margin_layer",
    "updated_pre_verdict",
    "apply_final_adaptive_veto",
]
