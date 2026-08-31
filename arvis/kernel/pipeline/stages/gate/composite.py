# arvis/kernel/pipeline/stages/gate/composite.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from arvis.errors.manager import ErrorManager
from arvis.kernel.pipeline.stages.gate.models import CompositeMetrics
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.lyapunov.lyapunov import (
    LyapunovState,
    lyapunov_value,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


def _is_valid_fast_state(value: Any) -> bool:
    """Structural validation for Lyapunov-compatible states."""
    return isinstance(value, float) or hasattr(value, "clamped")


def _fast_energy(value: Any) -> float:
    """Canonical coercion for fast Lyapunov energy: supports both
    float injections and LyapunovState runtime objects."""
    if isinstance(value, (float, int)):
        return float(value)

    return float(lyapunov_value(value))


def _coerce_fast_state(value: Any) -> LyapunovState:
    """Canonicalize a runtime value (state or injected raw energy)
    into a strict LyapunovState before entering the math layer."""
    if isinstance(value, LyapunovState):
        return value

    return LyapunovState.from_scalar(float(value))


def _is_valid_slow_state(value: Any) -> bool:
    """Structural validation for SlowState-compatible objects: absent
    is acceptable, a present value must be an actual SlowState."""
    return value is None or hasattr(value, "as_vector")


def compute_composite_metrics(ctx: CognitivePipelineContext) -> CompositeMetrics:
    """Composite W metrics from the canonical scientific context.

    Campaign STRUCT (LOT S4): the context is the real, typed pipeline
    context; the scientific sub-contexts are the single storage (the
    mirror double-writes through the accessor layer are gone).
    """
    composite_ctx = ctx.scientific.composite
    lyap_ctx = ctx.scientific.lyapunov
    regime_ctx = ctx.scientific.regime_state

    prev_slow = composite_ctx.prev_slow
    cur_slow = composite_ctx.cur_slow

    prev_symbolic = composite_ctx.prev_symbolic
    cur_symbolic = composite_ctx.cur_symbolic

    prev_lyap = lyap_ctx.prev_lyap
    cur_lyap = lyap_ctx.cur_lyap

    # ==========================================================
    # Explicit Lyapunov injection path
    #
    # Compliance/YAML scenarios inject states (and possibly an exact
    # delta) through the host extra channel; the gate preserves the
    # injected values instead of recomputing a synthetic composite
    # energy from partially initialized runtime state, so semantic
    # replay stays deterministic.
    # ==========================================================

    preserve_injected = bool(ctx.extra.get("preserve_injected_lyapunov", False))
    injected_delta = ctx.extra.get("delta_w")

    if preserve_injected and injected_delta is not None:
        delta = float(injected_delta)

        composite_ctx.delta_w = delta
        regime_ctx.stable = bool(delta <= 0.0)

        return CompositeMetrics(
            prev_slow=prev_slow,
            cur_slow=cur_slow,
            prev_symbolic=prev_symbolic,
            cur_symbolic=cur_symbolic,
            delta_w=delta,
            w_prev=composite_ctx.w_prev,
            w_current=composite_ctx.w_current,
        )

    if (
        prev_lyap is not None
        and cur_lyap is not None
        and _is_valid_fast_state(prev_lyap)
        and _is_valid_fast_state(cur_lyap)
        and _is_valid_slow_state(prev_slow)
        and _is_valid_slow_state(cur_slow)
    ):
        try:
            injected_w_prev = _fast_energy(prev_lyap)
            injected_w_current = _fast_energy(cur_lyap)

            injected_delta_w = injected_w_current - injected_w_prev

            composite_ctx.delta_w = injected_delta_w
            regime_ctx.stable = bool(injected_delta_w <= 0.0)

            return CompositeMetrics(
                prev_slow=prev_slow,
                cur_slow=cur_slow,
                prev_symbolic=prev_symbolic,
                cur_symbolic=cur_symbolic,
                delta_w=injected_delta_w,
                w_prev=float(injected_w_prev),
                w_current=float(injected_w_current),
            )
        except Exception as exc:
            ErrorManager.capture_exception(
                ctx,
                exc,
                code="composite_injected_compute_failure",
            )
    comp = CompositeLyapunov(lambda_mismatch=0.5, gamma_z=1.0)

    computed_delta_w: float | None = None
    computed_w_prev: float | None = None
    computed_w_current: float | None = None

    try:
        if (
            cur_lyap is not None
            and _is_valid_fast_state(cur_lyap)
            and _is_valid_slow_state(cur_slow)
        ):
            computed_w_current = comp.W(
                fast=_coerce_fast_state(cur_lyap),
                slow=cur_slow,
                symbolic=cur_symbolic if cur_symbolic is not None else None,
            )
        else:
            computed_w_current = 0.0

        if prev_lyap is not None:
            computed_w_prev = comp.W(
                fast=_coerce_fast_state(prev_lyap),
                slow=prev_slow,
                symbolic=prev_symbolic if prev_symbolic is not None else None,
            )

        if (
            prev_lyap is not None
            and cur_lyap is not None
            and _is_valid_fast_state(prev_lyap)
            and _is_valid_fast_state(cur_lyap)
            and _is_valid_slow_state(prev_slow)
            and _is_valid_slow_state(cur_slow)
        ):
            computed_delta_w = comp.delta_W(
                fast_prev=_coerce_fast_state(prev_lyap),
                fast_next=_coerce_fast_state(cur_lyap),
                slow_prev=prev_slow,
                slow_next=cur_slow,
                symbolic_prev=prev_symbolic if prev_symbolic is not None else None,
                symbolic_next=cur_symbolic if cur_symbolic is not None else None,
            )

        if computed_delta_w is None:
            computed_delta_w = 0.0
    except Exception as exc:
        computed_delta_w = composite_ctx.delta_w

        ErrorManager.capture_exception(
            ctx,
            exc,
            code="composite_delta_compute_failure",
        )

    return CompositeMetrics(
        prev_slow=prev_slow,
        cur_slow=cur_slow,
        prev_symbolic=prev_symbolic,
        cur_symbolic=cur_symbolic,
        delta_w=computed_delta_w,
        w_prev=computed_w_prev,
        w_current=computed_w_current,
    )


def expose_composite_metrics(
    ctx: CognitivePipelineContext, composite: CompositeMetrics
) -> None:
    scientific = ctx.scientific
    preserve_injected = bool(ctx.extra.get("preserve_injected_lyapunov", False))

    injected_delta = ctx.extra.get("delta_w")
    injected_stable = ctx.extra.get("stable")

    scientific.composite.w_prev = composite.w_prev
    scientific.composite.w_current = composite.w_current
    scientific.composite.prev_slow = composite.prev_slow
    scientific.composite.cur_slow = composite.cur_slow

    scientific.composite.prev_symbolic = composite.prev_symbolic
    scientific.composite.cur_symbolic = composite.cur_symbolic

    if preserve_injected and injected_delta is not None and composite.delta_w == 0.0:
        scientific.composite.delta_w = float(injected_delta)

        if injected_stable is not None:
            scientific.regime_state.stable = bool(injected_stable)
        return

    scientific.composite.delta_w = composite.delta_w

    if composite.delta_w is not None:
        scientific.regime_state.stable = bool(composite.delta_w <= 0.0)


def detect_recovery(
    ctx: CognitivePipelineContext,
    delta_w: float | None,
    w_prev: float | None,
    w_current: float | None,
) -> bool:
    prev_lyap = ctx.scientific.lyapunov.prev_lyap
    cur_lyap = ctx.scientific.lyapunov.cur_lyap

    recovery_detected = False
    try:
        if delta_w is not None and delta_w < 0:
            recovery_detected = True
        elif (
            prev_lyap is not None
            and cur_lyap is not None
            and _fast_energy(cur_lyap) < _fast_energy(prev_lyap)
        ):
            recovery_detected = True
        elif (
            w_prev is not None
            and w_current is not None
            and float(w_current) < float(w_prev)
        ):
            recovery_detected = True
    except Exception as exc:
        recovery_detected = False
        ErrorManager.capture_exception(
            ctx,
            exc,
            code="composite_recovery_detection_failure",
        )

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
    except (TypeError, ValueError, OverflowError):
        composite_recommendation = None
    return composite_recommendation


def detect_slow_drift(
    ctx: CognitivePipelineContext,
    prev_slow: Any,
    cur_slow: Any,
    delta_w: float | None,
) -> None:
    drift_ctx = ctx.scientific.drift
    lyap_ctx = ctx.scientific.lyapunov

    composite_ctx = ctx.scientific.composite
    prev_slow = (
        composite_ctx.prev_slow if composite_ctx.prev_slow is not None else prev_slow
    )
    cur_slow = (
        composite_ctx.cur_slow if composite_ctx.cur_slow is not None else cur_slow
    )

    prev_lyap = lyap_ctx.prev_lyap
    cur_lyap = lyap_ctx.cur_lyap

    try:
        # Fallback path when no structured slow-state exists.
        if prev_slow is None or cur_slow is None:
            hist = drift_ctx.lyap_history
            delta_hist = drift_ctx.lyap_delta_history

            if (
                cur_lyap is not None
                and _is_valid_fast_state(cur_lyap)
                and _is_valid_slow_state(cur_slow)
            ):
                cur_value = _fast_energy(cur_lyap)
                hist.append(cur_value)

                if prev_lyap is not None and _is_valid_fast_state(prev_lyap):
                    delta_hist.append(cur_value - _fast_energy(prev_lyap))

            if len(hist) > 20:
                hist.pop(0)
            if len(delta_hist) > 20:
                delta_hist.pop(0)

            diffs = delta_hist
            if not diffs and len(hist) >= 5:
                diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]

            small_increases = [d for d in diffs if 0 < d < 0.01]
            if len(small_increases) >= 4:
                drift_ctx.slow_drift_warning = True
        else:
            slow_delta = abs(cur_slow - prev_slow)
            drift_history = drift_ctx.slow_drift_history
            drift_history.append(slow_delta)
            if len(drift_history) > 10:
                drift_history.pop(0)
            avg_drift = sum(drift_history) / len(drift_history)
            if delta_w is not None and delta_w > 0 and avg_drift < 0.002:
                drift_ctx.slow_drift_warning = True
    except Exception as exc:
        ErrorManager.capture_exception(
            ctx,
            exc,
            code="slow_drift_detection_failure",
        )


__all__ = [
    "CompositeLyapunov",
    "compute_composite_metrics",
    "expose_composite_metrics",
    "detect_recovery",
    "compute_composite_recommendation",
    "detect_slow_drift",
]
