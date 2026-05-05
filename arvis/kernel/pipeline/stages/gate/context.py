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
