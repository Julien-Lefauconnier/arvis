# arvis/kernel/pipeline/stages/gate/switching.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.math.switching.switching_params import (
    kappa_eff,
    switching_condition,
    switching_lhs,
)


def compute_switching_safety(ctx: Any, overrides: GateOverrides) -> bool:
    switching_safe = True
    try:
        if not overrides.force_safe_switching:
            if ctx.switching_runtime and ctx.switching_params:
                switching_safe = switching_condition(
                    ctx.switching_runtime,
                    ctx.switching_params,
                )
    except Exception:
        switching_safe = True

    if overrides.force_safe_switching:
        switching_safe = True

    ctx.switching_safe = switching_safe
    return switching_safe


def build_switching_metrics(ctx: Any, switching_safe: bool) -> dict[str, Any]:
    try:
        if ctx.switching_runtime and ctx.switching_params:
            tau_d = float(ctx.switching_runtime.dwell_time())
            k_eff = float(kappa_eff(ctx.switching_params))
            lhs = float(switching_lhs(ctx.switching_runtime, ctx.switching_params))
            return {
                "tau_d": tau_d,
                "kappa_eff": k_eff,
                "lhs": lhs,
                "safe": bool(switching_safe),
                "J": float(ctx.switching_params.J),
                "eta": float(ctx.switching_params.eta),
                "alpha": float(ctx.switching_params.alpha),
                "gamma_z": float(ctx.switching_params.gamma_z),
                "L_T": float(ctx.switching_params.L_T),
            }
    except Exception:
        pass
    return {}


__all__ = [
    "switching_condition",
    "compute_switching_safety",
    "build_switching_metrics",
]
