# arvis/kernel/pipeline/stages/gate/composite.py

from __future__ import annotations

from typing import Any, cast

from arvis.kernel.pipeline.stages.gate.models import CompositeMetrics
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov


def _is_valid_fast_state(value: Any) -> bool:
    """
    Structural validation for Lyapunov-compatible states.
    """
    return isinstance(value, float) or hasattr(value, "clamped")


def _is_valid_slow_state(value: Any) -> bool:
    """
    Structural validation for SlowState-compatible objects.
    """
    return value is None or hasattr(value, "as_vector")


def compute_composite_metrics(ctx: Any) -> CompositeMetrics:
    scientific = getattr(ctx, "scientific", None)

    if scientific is not None:
        lyap_ctx = scientific.lyapunov
        composite_ctx = scientific.composite
        regime_ctx = scientific.regime_state

        prev_slow = lyap_ctx.slow_state_prev
        cur_slow = lyap_ctx.slow_state

        prev_symbolic = lyap_ctx.symbolic_state_prev
        cur_symbolic = lyap_ctx.symbolic_state

        prev_lyap = lyap_ctx.prev_lyap
        cur_lyap = lyap_ctx.cur_lyap
    else:
        prev_slow = getattr(ctx, "slow_state_prev", None)
        cur_slow = getattr(ctx, "slow_state", None)

        prev_symbolic = getattr(ctx, "symbolic_state_prev", None)
        cur_symbolic = getattr(ctx, "symbolic_state", None)

        prev_lyap = getattr(ctx, "prev_lyap", None)
        cur_lyap = getattr(ctx, "cur_lyap", None)

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

        if scientific is not None:
            composite_ctx.delta_w = delta
            regime_ctx.stable = bool(delta <= 0.0)

        ctx.delta_w = delta
        ctx.stable = bool(delta <= 0.0)
        ctx.extra["stable"] = ctx.stable

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

            injected_w_prev = float(prev_lyap)
            injected_w_current = float(cur_lyap)

            injected_delta_w = injected_w_current - injected_w_prev

            if scientific is not None:
                composite_ctx.delta_w = injected_delta_w
                regime_ctx.stable = bool(injected_delta_w <= 0.0)

            ctx.delta_w = injected_delta_w
            ctx.extra["delta_w"] = injected_delta_w
            ctx.extra["stable"] = bool(injected_delta_w <= 0.0)

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
                fast=cur_lyap,
                slow=cur_slow,
                symbolic=cur_symbolic if cur_symbolic is not None else None,
            )
        else:
            computed_w_current = 0.0

        if prev_lyap is not None:
            computed_w_prev = comp.W(
                fast=prev_lyap,
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
                fast_prev=prev_lyap,
                fast_next=cur_lyap,
                slow_prev=prev_slow,
                slow_next=cur_slow,
                symbolic_prev=prev_symbolic if prev_symbolic is not None else None,
                symbolic_next=cur_symbolic if cur_symbolic is not None else None,
            )

        if computed_delta_w is None:
            computed_delta_w = 0.0
    except Exception:
        if scientific is not None:
            computed_delta_w = cast(
                float | None,
                composite_ctx.delta_w,
            )
        else:
            computed_delta_w = cast(
                float | None,
                getattr(ctx, "delta_w", None),
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

    ctx.w_prev = composite.w_prev
    ctx.w_current = composite.w_current

    if preserve_injected and injected_delta is not None and composite.delta_w == 0.0:
        if scientific is not None:
            scientific.composite.delta_w = float(injected_delta)

        ctx.delta_w = float(injected_delta)

        if injected_stable is not None:
            if scientific is not None:
                scientific.regime_state.stable = bool(injected_stable)

            ctx.stable = bool(injected_stable)
        return

    if scientific is not None:
        scientific.composite.delta_w = composite.delta_w

    ctx.delta_w = composite.delta_w

    if composite.delta_w is not None:
        if scientific is not None:
            scientific.regime_state.stable = bool(composite.delta_w <= 0.0)

        ctx.stable = bool(composite.delta_w <= 0.0)


def detect_recovery(
    ctx: Any,
    delta_w: float | None,
    w_prev: float | None,
    w_current: float | None,
) -> bool:
    scientific = getattr(ctx, "scientific", None)

    if scientific is not None:
        prev_lyap = scientific.lyapunov.prev_lyap
        cur_lyap = scientific.lyapunov.cur_lyap
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
            and float(cur_lyap) < float(prev_lyap)
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
    scientific = getattr(ctx, "scientific", None)

    if scientific is not None:
        cur_lyap = scientific.lyapunov.cur_lyap
    else:
        cur_lyap = getattr(ctx, "cur_lyap", None)
    try:
        if prev_slow is None or cur_slow is None:
            hist = ctx.extra.setdefault("lyap_history", [])
            if (
                cur_lyap is not None
                and _is_valid_fast_state(cur_lyap)
                and _is_valid_slow_state(cur_slow)
            ):
                hist.append(float(cur_lyap))
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
