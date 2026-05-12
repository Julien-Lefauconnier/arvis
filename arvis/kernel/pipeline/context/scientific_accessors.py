# arvis/kernel/pipeline/context/scientific_accessors.py

from __future__ import annotations

from typing import Any, cast

from arvis.kernel.pipeline.context.scientific_context import (
    PipelineScientificContext,
)
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.state.symbolic_state import (
    SymbolicState,
)


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


def set_prev_lyap(ctx: Any, value: LyapunovState | float | None) -> None:
    scientific(ctx).lyapunov.prev_lyap = value


def cur_lyap(ctx: Any) -> LyapunovState | float | None:
    return scientific(ctx).lyapunov.cur_lyap


def set_cur_lyap(ctx: Any, value: LyapunovState | float | None) -> None:
    scientific(ctx).lyapunov.cur_lyap = value


def delta_w(ctx: Any) -> float | None:
    return scientific(ctx).composite.delta_w


def set_delta_w(ctx: Any, value: float | None) -> None:
    scientific(ctx).composite.delta_w = value


def w_prev(ctx: Any) -> float | None:
    return scientific(ctx).composite.w_prev


def set_w_prev(ctx: Any, value: float | None) -> None:
    scientific(ctx).composite.w_prev = value


def w_current(ctx: Any) -> float | None:
    return scientific(ctx).composite.w_current


def set_w_current(ctx: Any, value: float | None) -> None:
    scientific(ctx).composite.w_current = value


def stable(ctx: Any) -> bool | None:
    runtime = getattr(ctx, "scientific", None)

    if runtime is not None:
        value = runtime.regime_state.stable
        return bool(value) if value is not None else None

    return getattr(ctx, "stable", None)


def set_stable(ctx: Any, value: bool | None) -> None:
    scientific(ctx).regime_state.stable = value


def prev_slow(ctx: Any) -> SlowState | None:
    return scientific(ctx).composite.prev_slow


def cur_slow(ctx: Any) -> SlowState | None:
    return scientific(ctx).composite.cur_slow


def prev_symbolic(ctx: Any) -> SymbolicState | None:
    return scientific(ctx).composite.prev_symbolic


def cur_symbolic(ctx: Any) -> SymbolicState | None:
    return scientific(ctx).composite.cur_symbolic


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
    return ctx.scientific.core.drift_score


def uncertainty(ctx: Any) -> Any:
    return ctx.scientific.core.uncertainty


def uncertainty_intent(ctx: Any) -> Any:
    return ctx.scientific.core.uncertainty_intent


# ============================================================
# REGIME
# ============================================================


def regime(ctx: Any) -> Any:
    return ctx.scientific.regime_state.regime


def regime_confidence(ctx: Any) -> Any:
    return ctx.scientific.regime_state.regime_confidence


def theoretical_regime(ctx: Any) -> Any:
    return ctx.scientific.regime_state.theoretical_regime


def fast_dynamics(ctx: Any) -> Any:
    return ctx.scientific.regime_state.fast_dynamics


def perturbation(ctx: Any) -> Any:
    return ctx.scientific.regime_state.perturbation


# ============================================================
# LYAPUNOV
# ============================================================


def symbolic_state(ctx: Any) -> Any:
    return ctx.scientific.lyapunov.symbolic_state


def quadratic_lyap_snapshot(ctx: Any) -> Any:
    return ctx.scientific.lyapunov.quadratic_lyap_snapshot


def quadratic_comparability(ctx: Any) -> Any:
    return ctx.scientific.lyapunov.quadratic_comparability
