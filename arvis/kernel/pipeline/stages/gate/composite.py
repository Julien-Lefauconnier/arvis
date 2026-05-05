# arvis/kernel/pipeline/stages/gate/composite.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.stages.gate.models import CompositeMetrics
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov


def compute_composite_metrics(ctx: Any) -> CompositeMetrics:
    comp = CompositeLyapunov(lambda_mismatch=0.5, gamma_z=1.0)

    prev_slow = getattr(ctx, "slow_state_prev", None)
    cur_slow = getattr(ctx, "slow_state", None)
    prev_symbolic = getattr(ctx, "symbolic_state_prev", None)
    cur_symbolic = getattr(ctx, "symbolic_state", None)

    delta_w: float | None = None
    w_prev: float | None = None
    w_current: float | None = None

    try:
        if ctx.cur_lyap is not None:
            w_current = comp.W(
                fast=ctx.cur_lyap,
                slow=cur_slow,
                symbolic=cur_symbolic if cur_symbolic is not None else None,
            )
        else:
            w_current = 0.0

        if ctx.prev_lyap is not None:
            w_prev = comp.W(
                fast=ctx.prev_lyap,
                slow=prev_slow,
                symbolic=prev_symbolic if prev_symbolic is not None else None,
            )

        if ctx.prev_lyap is not None and ctx.cur_lyap is not None:
            delta_w = comp.delta_W(
                fast_prev=ctx.prev_lyap,
                fast_next=ctx.cur_lyap,
                slow_prev=prev_slow,
                slow_next=cur_slow,
                symbolic_prev=prev_symbolic if prev_symbolic is not None else None,
                symbolic_next=cur_symbolic if cur_symbolic is not None else None,
            )

        if delta_w is None:
            delta_w = 0.0
    except Exception:
        delta_w = getattr(ctx, "delta_w", None)

    return CompositeMetrics(
        prev_slow=prev_slow,
        cur_slow=cur_slow,
        prev_symbolic=prev_symbolic,
        cur_symbolic=cur_symbolic,
        delta_w=delta_w,
        w_prev=w_prev,
        w_current=w_current,
    )


def expose_composite_metrics(ctx: Any, composite: CompositeMetrics) -> None:
    ctx.w_prev = composite.w_prev
    ctx.w_current = composite.w_current
    ctx.delta_w = composite.delta_w


def detect_recovery(
    ctx: Any,
    delta_w: float | None,
    w_prev: float | None,
    w_current: float | None,
) -> bool:
    recovery_detected = False
    try:
        if delta_w is not None and delta_w < 0:
            recovery_detected = True
        elif (
            ctx.prev_lyap is not None
            and ctx.cur_lyap is not None
            and float(ctx.cur_lyap) < float(ctx.prev_lyap)
        ):
            recovery_detected = True
        elif (
            w_prev is not None
            and w_current is not None
            and float(w_current) < float(w_prev)
        ):
            recovery_detected = True
    except Exception:
        recovery_detected = False

    return recovery_detected


def compute_composite_recommendation(
    pipeline: Any,
    delta_w: float | None,
    w_current: float | None,
) -> str | None:
    composite_recommendation = None
    try:
        if delta_w is not None and w_current is not None:
            denom = max(abs(w_current), 1e-6)
            raw_ratio = delta_w / denom
            ratio = max(min(raw_ratio, 1.0), -1.0)

            rec_soft = getattr(pipeline, "composite_rec_soft_threshold", 0.0)
            rec_strong = getattr(pipeline, "composite_rec_strong_threshold", 0.05)

            if ratio > rec_strong:
                composite_recommendation = "strong_decrease"
            elif ratio > rec_soft:
                composite_recommendation = "soft_decrease"
            elif ratio < -rec_strong:
                composite_recommendation = "strong_increase"
            else:
                composite_recommendation = "stable"
    except Exception:
        composite_recommendation = None
    return composite_recommendation


def detect_slow_drift(
    ctx: Any,
    prev_slow: Any,
    cur_slow: Any,
    delta_w: float | None,
) -> None:
    try:
        if prev_slow is None or cur_slow is None:
            hist = ctx.extra.setdefault("lyap_history", [])
            if ctx.cur_lyap is not None:
                hist.append(float(ctx.cur_lyap))
            if len(hist) > 20:
                hist.pop(0)
            if len(hist) >= 5:
                diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
                small_increases = [d for d in diffs if d > 0 and d < 0.01]
                if len(small_increases) >= 4:
                    ctx.extra["slow_drift_warning"] = True
        else:
            slow_delta = abs(cur_slow - prev_slow)
            drift_history = ctx.extra.setdefault("slow_drift_history", [])
            drift_history.append(slow_delta)
            if len(drift_history) > 10:
                drift_history.pop(0)
            avg_drift = sum(drift_history) / len(drift_history)
            if delta_w is not None and delta_w > 0 and avg_drift < 0.002:
                ctx.extra["slow_drift_warning"] = True
    except Exception:
        pass


__all__ = [
    "CompositeLyapunov",
    "compute_composite_metrics",
    "expose_composite_metrics",
    "detect_recovery",
    "compute_composite_recommendation",
    "detect_slow_drift",
]
