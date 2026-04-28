# arvis/math/gate/gate_fusion.py

from __future__ import annotations

from typing import Any

from arvis.math.decision.multiaxial_fusion import MultiaxialInputs, multiaxial_fusion


def run_fusion(
    *,
    pre_verdict: Any,
    delta_w: float | None,
    switching_safe: bool,
    global_safe: bool,
    ctx: Any,
) -> Any:
    inputs = MultiaxialInputs(
        fast_verdict=pre_verdict,
        delta_w=delta_w,
        switching_safe=switching_safe,
        global_safe=global_safe,
    )
    return multiaxial_fusion(inputs)
