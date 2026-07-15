# arvis/kernel/pipeline/stages/gate/composite.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.kernel.pipeline.context.scientific_accessors import (
    cur_lyap as get_cur_lyap,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    cur_slow as get_cur_slow,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    cur_symbolic as get_cur_symbolic,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    prev_lyap as get_prev_lyap,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    prev_slow as get_prev_slow,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    prev_symbolic as get_prev_symbolic,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    scientific,
    set_delta_w,
    set_stable,
    set_w_current,
    set_w_prev,
)
from arvis.kernel.pipeline.stages.gate.models import CompositeMetrics
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.lyapunov.lyapunov import (
    LyapunovState,
    lyapunov_value,
)


def _is_valid_fast_state(value: Any) -> bool:
    """
    Structural validation for Lyapunov-compatible states.
    """
    return isinstance(value, float) or hasattr(value, "clamped")


def _fast_energy(value: Any) -> float:
    """
    Canonical coercion helper for fast Lyapunov energy.

    Transitional compatibility:
    supports both float injections and LyapunovState runtime objects.
    """
    if isinstance(value, (float, int)):
        return float(value)

    return float(lyapunov_value(value))


def _coerce_fast_state(value: Any) -> LyapunovState:
    """
    Transitional compatibility adapter.

    CompositeLyapunov internally expects a LyapunovState,
    but runtime/compliance paths may still inject raw float
    Lyapunov energies.

    This helper canonicalizes the runtime value into a strict
    LyapunovState object before entering the math layer.
    """
    if isinstance(value, LyapunovState):
        return value

    return LyapunovState.from_scalar(float(value))


def _is_valid_slow_state(value: Any) -> bool:
    """
    Structural validation for SlowState-compatible objects.
    """
    return value is None or hasattr(value, "as_vector")


def compute_composite_metrics(ctx: Any) -> CompositeMetrics:
    runtime = scientific(ctx)

    composite_ctx = runtime.composite
    regime_ctx = runtime.regime_state

    prev_slow = get_prev_slow(ctx)
    cur_slow = get_cur_slow(ctx)

    prev_symbolic = get_prev_symbolic(ctx)
    cur_symbolic = get_cur_symbolic(ctx)

    prev_lyap = get_prev_lyap(ctx)
    cur_lyap = get_cur_lyap(ctx)

    # ==========================================================
    # Explicit Lyapunov injection path
    #
    # Compliance/YAML scenarios may directly inject:
    #   - ctx.prev_lyap
    #   - ctx.cur_lyap
    #
    # In this case we must compute the composite energy directly
    # from these states and expose the resulting delta_w back into
    # the runtime context.
    #
    # Without this explicit path, the gate stack may incorrectly
    # fall back to synthetic/default values and downgrade nominal
    # local scenarios into REQUIRE_CONFIRMATION.
    # ==========================================================

    preserve_injected = bool(
        getattr(ctx, "extra", {}).get("preserve_injected_lyapunov", False)
    )
    injected_delta = getattr(ctx, "extra", {}).get("delta_w")

    if preserve_injected and injected_delta is not None:
        delta = float(injected_delta)

        composite_ctx.delta_w = delta
        regime_ctx.stable = bool(delta <= 0.0)

        set_delta_w(ctx, delta)
        set_stable(ctx, bool(delta <= 0.0))

        return CompositeMetrics(
            prev_slow=prev_slow,
            cur_slow=cur_slow,
            prev_symbolic=prev_symbolic,
            cur_symbolic=cur_symbolic,
            delta_w=delta,
            w_prev=getattr(ctx, "w_prev", None),
            w_current=getattr(ctx, "w_current", None),
        )

    if (
        prev_lyap is not None
        and cur_lyap is not None
        and _is_valid_fast_state(prev_lyap)
        and _is_valid_fast_state(cur_lyap)
        and _is_valid_slow_state(prev_slow)
        and _is_valid_slow_state(cur_slow)
    ):
        comp = CompositeLyapunov(lambda_mismatch=0.5, gamma_z=1.0)

        try:
            # ----------------------------------------------------------
            # Explicit compliance/YAML injection path

            # In compliance scenarios we preserve the exact injected
            # Lyapunov delta instead of recomputing a synthetic
            # composite energy from partially initialized runtime state.

            # This guarantees deterministic semantic replay between:

            # YAML scenario
            # -> pipeline context
            # -> gate kernel

            # without introducing hidden slow/symbolic reconstruction
            # drift.
            # ----------------------------------------------------------

            injected_w_prev = _fast_energy(prev_lyap)
            injected_w_current = _fast_energy(cur_lyap)

            injected_delta_w = injected_w_current - injected_w_prev

            composite_ctx.delta_w = injected_delta_w
            regime_ctx.stable = bool(injected_delta_w <= 0.0)

            set_delta_w(ctx, injected_delta_w)
            set_stable(ctx, bool(injected_delta_w <= 0.0))

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
            ctx.extra["composite_injected_error"] = repr(exc)
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


def expose_composite_metrics(ctx: Any, composite: CompositeMetrics) -> None:
    scientific = getattr(ctx, "scientific", None)
    preserve_injected = bool(
        getattr(ctx, "extra", {}).get("preserve_injected_lyapunov", False)
    )

    injected_delta = getattr(ctx, "extra", {}).get("delta_w")
    injected_stable = getattr(ctx, "extra", {}).get("stable")

    if scientific is not None:
        scientific.composite.w_prev = composite.w_prev
        scientific.composite.w_current = composite.w_current
        scientific.composite.prev_slow = composite.prev_slow
        scientific.composite.cur_slow = composite.cur_slow

        scientific.composite.prev_symbolic = composite.prev_symbolic
        scientific.composite.cur_symbolic = composite.cur_symbolic

    set_w_prev(ctx, composite.w_prev)
    set_w_current(ctx, composite.w_current)

    if preserve_injected and injected_delta is not None and composite.delta_w == 0.0:
        if scientific is not None:
            scientific.composite.delta_w = float(injected_delta)

        set_delta_w(ctx, float(injected_delta))

        if injected_stable is not None:
            set_stable(ctx, bool(injected_stable))
        return

    if scientific is not None:
        scientific.composite.delta_w = composite.delta_w

    set_delta_w(ctx, composite.delta_w)

    if composite.delta_w is not None:
        set_stable(ctx, bool(composite.delta_w <= 0.0))


def detect_recovery(
    ctx: Any,
    delta_w: float | None,
    w_prev: float | None,
    w_current: float | None,
) -> bool:
    runtime = getattr(ctx, "scientific", None)

    if runtime is not None:
        prev_lyap = get_prev_lyap(ctx)
        cur_lyap = get_cur_lyap(ctx)
    else:
        prev_lyap = getattr(ctx, "prev_lyap", None)
        cur_lyap = getattr(ctx, "cur_lyap", None)
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
    ctx: Any,
    prev_slow: Any,
    cur_slow: Any,
    delta_w: float | None,
) -> None:
    runtime = getattr(ctx, "scientific", None)

    if runtime is not None:
        composite_ctx = runtime.composite
        lyap_ctx = runtime.lyapunov
        drift_ctx = runtime.drift

        prev_slow = (
            composite_ctx.prev_slow
            if composite_ctx.prev_slow is not None
            else prev_slow
        )

        cur_slow = (
            composite_ctx.cur_slow if composite_ctx.cur_slow is not None else cur_slow
        )

        prev_lyap = lyap_ctx.prev_lyap
        cur_lyap = lyap_ctx.cur_lyap
    else:
        drift_ctx = None
        prev_lyap = getattr(ctx, "prev_lyap", None)
        cur_lyap = getattr(ctx, "cur_lyap", None)
    try:
        # Fallback path when no structured slow-state exists.
        if prev_slow is None or cur_slow is None:
            hist = (
                drift_ctx.lyap_history
                if drift_ctx is not None
                else ctx.extra.setdefault("lyap_history", [])
            )
            delta_hist = (
                drift_ctx.lyap_delta_history
                if drift_ctx is not None
                else ctx.extra.setdefault("lyap_delta_history", [])
            )

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
                if drift_ctx is not None:
                    drift_ctx.slow_drift_warning = True
                ctx.extra["slow_drift_warning"] = True
        else:
            slow_delta = abs(cur_slow - prev_slow)
            drift_history = (
                drift_ctx.slow_drift_history
                if drift_ctx is not None
                else ctx.extra.setdefault("slow_drift_history", [])
            )
            drift_history.append(slow_delta)
            if len(drift_history) > 10:
                drift_history.pop(0)
            avg_drift = sum(drift_history) / len(drift_history)
            if delta_w is not None and delta_w > 0 and avg_drift < 0.002:
                if drift_ctx is not None:
                    drift_ctx.slow_drift_warning = True
                ctx.extra["slow_drift_warning"] = True
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
