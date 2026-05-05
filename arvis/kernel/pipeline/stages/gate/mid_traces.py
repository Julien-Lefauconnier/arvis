# arvis/kernel/pipeline/stages/gate/mid_traces.py

from __future__ import annotations

from typing import Any

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def write_mid_traces(
    ctx: Any,
    w_current: float | None,
    delta_w: float | None,
    pre_verdict: LyapunovVerdict,
    verdict: LyapunovVerdict,
) -> None:
    try:
        if delta_w is not None:
            ctx.extra["closed_loop_feedback"] = {
                "energy_increase": bool(delta_w > 0),
                "energy_decrease": bool(delta_w < 0),
                "control_should_reduce": bool(delta_w > 0),
            }
    except Exception:
        pass

    try:
        ctx.extra["iss_perturbation"] = {
            "projection": float(getattr(ctx, "projection_disturbance", 0.0) or 0.0),
            "noise": float(getattr(ctx, "noise_disturbance", 0.0) or 0.0),
            "switch": float(getattr(ctx, "switching_disturbance", 0.0) or 0.0),
            "adversarial": float(getattr(ctx, "adversarial_disturbance", 0.0) or 0.0),
        }
    except Exception:
        pass

    try:
        if ctx.validity_envelope is not None:
            ctx.extra["validity_envelope_extended"] = {
                **ctx.extra.get("validity_envelope", {}),
                "projection_valid": bool(
                    ctx.prev_lyap is not None or ctx.cur_lyap is not None
                ),
                "switching_constraints_valid": bool(
                    getattr(ctx, "switching_safe", False)
                ),
                "perturbation_bounded": True,
            }
    except Exception:
        pass
