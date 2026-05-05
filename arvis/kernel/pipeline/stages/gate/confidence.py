# arvis/kernel/pipeline/stages/gate/confidence.py

from __future__ import annotations

from typing import Any

from arvis.math.confidence.system_confidence import (
    SystemConfidenceInputs,
    compute_system_confidence,
)


def compute_gate_system_confidence(
    ctx: Any,
    delta_w: float | None,
    global_safe: bool,
    switching_safe: bool,
) -> tuple[SystemConfidenceInputs, float]:
    confidence_inputs = SystemConfidenceInputs(
        delta_w=delta_w,
        global_safe=bool(global_safe),
        switching_safe=bool(switching_safe),
        has_history=ctx.prev_lyap is not None,
        has_observability=ctx.cur_lyap is not None,
        collapse_risk=float(getattr(ctx, "collapse_risk", 0.0) or 0.0),
    )
    system_confidence = compute_system_confidence(confidence_inputs)
    ctx.extra["system_confidence"] = system_confidence
    ctx.system_confidence = system_confidence
    return confidence_inputs, system_confidence
