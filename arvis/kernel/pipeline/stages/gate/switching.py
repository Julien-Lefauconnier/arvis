# arvis/kernel/pipeline/stages/gate/switching.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.errors.pipeline import PipelineStageDegradedError
from arvis.kernel.pipeline.context.scientific_accessors import (
    scientific as scientific_of,
)
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
            switching_ctx = scientific_of(ctx).switching
            if switching_ctx.switching_runtime and switching_ctx.switching_params:
                switching_safe = switching_condition(
                    switching_ctx.switching_runtime,
                    switching_ctx.switching_params,
                )
    except Exception as exc:
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "compute_switching_safety",
                    "fallback": "switching_safe=False (fail-closed)",
                    "exception_type": type(exc).__name__,
                },
            ),
        )
        # F-002: unknown switching safety is not safe (fail-closed).
        switching_safe = False

    if overrides.force_safe_switching:
        switching_safe = True

    scientific_of(ctx).switching.switching_safe = switching_safe
    return switching_safe


def build_switching_metrics(ctx: Any, switching_safe: bool) -> dict[str, Any]:
    try:
        switching_ctx = scientific_of(ctx).switching
        if switching_ctx.switching_runtime and switching_ctx.switching_params:
            params = switching_ctx.switching_params
            tau_d = float(switching_ctx.switching_runtime.dwell_time())
            k_eff = float(kappa_eff(params))
            lhs = float(switching_lhs(switching_ctx.switching_runtime, params))
            return {
                "tau_d": tau_d,
                "kappa_eff": k_eff,
                "lhs": lhs,
                "safe": bool(switching_safe),
                "J": float(params.J),
                "eta": float(params.eta),
                "alpha": float(params.alpha),
                "gamma_z": float(params.gamma_z),
                "L_T": float(params.L_T),
            }
    except Exception as exc:
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "build_switching_metrics",
                    "exception_type": type(exc).__name__,
                },
            ),
        )
    return {}


__all__ = [
    "switching_condition",
    "compute_switching_safety",
    "build_switching_metrics",
]
