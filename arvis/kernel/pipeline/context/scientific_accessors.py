# arvis/kernel/pipeline/context/scientific_accessors.py

from __future__ import annotations

from typing import Any, cast

from arvis.kernel.pipeline.context.scientific_context import (
    PipelineScientificContext,
)
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov import LyapunovState


def scientific(ctx: Any) -> PipelineScientificContext:
    """
    Return the canonical scientific runtime context.

    Transitional compatibility:
    legacy/mock contexts may not yet expose ctx.scientific.
    """
    runtime = getattr(ctx, "scientific", None)

    if runtime is None:
        runtime = PipelineScientificContext()
        ctx.scientific = runtime
    elif not isinstance(runtime, PipelineScientificContext):
        raise TypeError("ctx.scientific must be a PipelineScientificContext")

    return runtime


def prev_lyap(ctx: Any) -> LyapunovState | float | None:
    return scientific(ctx).lyapunov.prev_lyap


def cur_lyap(ctx: Any) -> LyapunovState | float | None:
    return scientific(ctx).lyapunov.cur_lyap


def delta_w(ctx: Any) -> float | None:
    return scientific(ctx).composite.delta_w


def stable(ctx: Any) -> bool | None:
    runtime = getattr(ctx, "scientific", None)

    if runtime is not None:
        value = runtime.regime_state.stable
        return bool(value) if value is not None else None

    return getattr(ctx, "stable", None)


def adaptive_snapshot(ctx: Any) -> AdaptiveSnapshot | None:
    """
    Transitional accessor.

    Priority:
    1. structured scientific runtime
    2. legacy root-level compatibility

    Transitional compatibility:
    legacy tests may inject lightweight mock objects
    exposing AdaptiveSnapshot-compatible attributes.
    """

    runtime = getattr(ctx, "scientific", None)

    if runtime is not None:
        value = runtime.adaptive.adaptive_snapshot

        if value is not None:
            return cast(AdaptiveSnapshot, value)

    return getattr(ctx, "adaptive_snapshot", None)


def set_adaptive_snapshot(
    ctx: Any,
    snapshot: AdaptiveSnapshot | None,
) -> None:
    scientific(ctx).adaptive.adaptive_snapshot = snapshot


# ============================================================
# CORE SIGNALS
# ============================================================


def collapse_risk(ctx: Any) -> Any:
    return scientific(ctx).core.collapse_risk


def drift_score(ctx: Any) -> Any:
    return scientific(ctx).core.drift_score


def uncertainty(ctx: Any) -> Any:
    return scientific(ctx).core.uncertainty


# ============================================================
# REGIME
# ============================================================


def regime(ctx: Any) -> Any:
    return scientific(ctx).regime_state.regime


def theoretical_regime(ctx: Any) -> Any:
    return scientific(ctx).regime_state.theoretical_regime


def fast_dynamics(ctx: Any) -> Any:
    return scientific(ctx).regime_state.fast_dynamics


def perturbation(ctx: Any) -> Any:
    return scientific(ctx).regime_state.perturbation


# ============================================================
# LYAPUNOV
# ============================================================


def symbolic_state(ctx: Any) -> Any:
    return scientific(ctx).lyapunov.symbolic_state


def quadratic_lyap_snapshot(ctx: Any) -> Any:
    return scientific(ctx).lyapunov.quadratic_lyap_snapshot


def quadratic_comparability(ctx: Any) -> Any:
    return scientific(ctx).lyapunov.quadratic_comparability


# ============================================================
# SWITCHING / COMPOSITE HISTORY
# ============================================================


def switching_safe(ctx: Any) -> Any:
    return scientific(ctx).switching.switching_safe


def delta_w_history(ctx: Any) -> list[float]:
    return scientific(ctx).composite.delta_w_history


# ============================================================
# ADAPTIVE
# ============================================================
