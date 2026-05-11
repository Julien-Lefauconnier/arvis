# arvis/kernel/pipeline/stages/gate/context.py

from __future__ import annotations

import logging
from typing import Any, cast

from arvis.kernel.pipeline.context.scientific_accessors import (
    set_cur_lyap,
    set_delta_w,
    set_prev_lyap,
    set_stable,
    set_w_current,
    set_w_prev,
)
from arvis.kernel.pipeline.gate_overrides import GateOverrides


def resolve_overrides(ctx: Any) -> GateOverrides:
    overrides = getattr(ctx, "gate_overrides", None)
    if overrides is not None:
        return cast(GateOverrides, overrides)

    extra = getattr(ctx, "extra", {})
    return GateOverrides(
        force_safe_projection=extra.get("force_safe_projection", False),
        force_safe_switching=extra.get("force_safe_switching", False),
    )


def _sync_legacy_runtime_mirrors(ctx: Any) -> None:
    """
    Legacy mirror synchronization removed.
    Scientific runtime is canonical.
    """
    return


def initialize_context(ctx: Any) -> logging.Logger:
    # -----------------------------------------------------
    # # Transitional scientific hydration for legacy/mock contexts
    # -----------------------------------------------------

    runtime = getattr(ctx, "scientific", None)

    # -----------------------------------------------------
    # Transitional compatibility bootstrap
    #
    # Legacy tests and lightweight mock contexts may not
    # expose a structured scientific runtime yet.
    #
    # Runtime ownership remains canonical once hydrated.
    # -----------------------------------------------------

    if runtime is None:
        from arvis.kernel.pipeline.context.scientific_context import (
            PipelineScientificContext,
        )

        runtime = PipelineScientificContext()
        ctx.scientific = runtime
    # ---------------------------------------------
    # Transitional scientific hydration
    # ---------------------------------------------

    if runtime.composite.w_prev is None:
        runtime.composite.w_prev = getattr(
            ctx,
            "w_prev",
            None,
        )

    if runtime.composite.w_current is None:
        runtime.composite.w_current = getattr(
            ctx,
            "w_current",
            0.0,
        )

    if runtime.composite.delta_w is None:
        runtime.composite.delta_w = getattr(
            ctx,
            "delta_w",
            0.0,
        )

    if runtime.composite.delta_w_history is None:
        runtime.composite.delta_w_history = getattr(
            ctx,
            "delta_w_history",
            [],
        )

    if runtime.regime_state.stable is None:
        runtime.regime_state.stable = getattr(
            ctx,
            "stable",
            None,
        )

    if runtime.regime_state.regime is None:
        runtime.regime_state.regime = getattr(
            ctx,
            "regime",
            None,
        )

    if runtime.switching.switching_safe is None:
        runtime.switching.switching_safe = getattr(
            ctx,
            "switching_safe",
            None,
        )

    if not runtime.switching.switching_metrics:
        runtime.switching.switching_metrics = getattr(
            ctx,
            "switching_metrics",
            {},
        )

    set_prev_lyap(
        ctx,
        getattr(ctx, "prev_lyap", None),
    )

    set_cur_lyap(
        ctx,
        getattr(ctx, "cur_lyap", None),
    )

    runtime.switching.switching_runtime = getattr(
        ctx,
        "switching_runtime",
        None,
    )

    runtime.switching.switching_params = getattr(
        ctx,
        "switching_params",
        None,
    )

    runtime.adaptive.global_stability_metrics = getattr(
        ctx,
        "global_stability_metrics",
        None,
    )

    runtime.adaptive.validity_envelope = getattr(
        ctx,
        "validity_envelope",
        None,
    )

    runtime.adaptive.adaptive_snapshot = getattr(
        ctx,
        "adaptive_snapshot",
        None,
    )

    runtime.composite.prev_slow = getattr(ctx, "slow_state_prev", None)
    runtime.composite.cur_slow = getattr(ctx, "slow_state", None)

    runtime.composite.prev_symbolic = getattr(ctx, "symbolic_state_prev", None)
    runtime.composite.cur_symbolic = getattr(ctx, "symbolic_state", None)

    ctx.scientific = runtime

    # -----------------------------------------------------
    # Transitional hydration for pre-existing scientific ctx
    # -----------------------------------------------------

    if hasattr(ctx, "prev_lyap"):
        set_prev_lyap(ctx, getattr(ctx, "prev_lyap", None))

    if hasattr(ctx, "cur_lyap"):
        set_cur_lyap(ctx, getattr(ctx, "cur_lyap", None))

    if runtime.composite.prev_slow is None:
        runtime.composite.prev_slow = getattr(
            ctx,
            "slow_state_prev",
            None,
        )

    if runtime.composite.cur_slow is None:
        runtime.composite.cur_slow = getattr(
            ctx,
            "slow_state",
            None,
        )

    if runtime.composite.prev_symbolic is None:
        runtime.composite.prev_symbolic = getattr(
            ctx,
            "symbolic_state_prev",
            None,
        )

    if runtime.composite.cur_symbolic is None:
        runtime.composite.cur_symbolic = getattr(
            ctx,
            "symbolic_state",
            None,
        )

    if not hasattr(ctx, "extra"):
        ctx.extra = {}

    # -----------------------------------------------------
    # Composite scientific runtime ownership
    # -----------------------------------------------------

    composite = runtime.composite

    if composite.delta_w_history is None:
        composite.delta_w_history = []

    composite.w_prev = composite.w_prev
    if composite.w_current is None:
        composite.w_current = 0.0

    if composite.delta_w is None:
        composite.delta_w = 0.0

    # -----------------------------------------------------
    # Preserve injected compliance/runtime values
    # -----------------------------------------------------

    if ctx.extra.get("preserve_injected_lyapunov", False):
        injected_delta = ctx.extra.get("delta_w")
        injected_stable = ctx.extra.get("stable")

        if injected_delta is not None:
            set_delta_w(ctx, float(injected_delta))

        if injected_stable is not None:
            set_stable(ctx, bool(injected_stable))

    set_w_prev(ctx, composite.w_prev)
    set_w_current(ctx, composite.w_current)
    set_delta_w(ctx, composite.delta_w)

    _sync_legacy_runtime_mirrors(ctx)

    # Drift compatibility mirrors.
    ctx.extra.setdefault("lyap_history", runtime.drift.lyap_history)
    ctx.extra.setdefault("lyap_delta_history", runtime.drift.lyap_delta_history)
    ctx.extra.setdefault("slow_drift_history", runtime.drift.slow_drift_history)

    ctx.stability_certificate = getattr(
        ctx,
        "stability_certificate",
        {
            "local": False,
            "global": True,
            "switching": True,
            "delta_negative": True,
            "exponential": True,
        },
    )

    ctx.system_confidence = getattr(ctx, "system_confidence", 0.0)

    return logging.getLogger(__name__)
