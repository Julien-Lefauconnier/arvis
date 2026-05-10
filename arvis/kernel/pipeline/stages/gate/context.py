# arvis/kernel/pipeline/stages/gate/context.py

from __future__ import annotations

import logging
from typing import Any, cast

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


def initialize_context(ctx: Any) -> logging.Logger:
    if not hasattr(ctx, "delta_w_history"):
        ctx.delta_w_history = []

    if not hasattr(ctx, "extra"):
        ctx.extra = {}

    ctx.w_prev = getattr(ctx, "w_prev", None)
    ctx.w_current = getattr(ctx, "w_current", 0.0)
    ctx.delta_w = getattr(ctx, "delta_w", 0.0)

    # Preserve explicit Lyapunov injections from compliance/YAML builders.
    # Some preparation stages may leave canonical attrs at default values
    # while the injected values are still available in ctx.extra.
    if ctx.extra.get("preserve_injected_lyapunov", False):
        injected_delta = ctx.extra.get("delta_w")
        injected_stable = ctx.extra.get("stable")

        if injected_delta is not None:
            ctx.delta_w = float(injected_delta)
        if injected_stable is not None:
            ctx.stable = bool(injected_stable)

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
