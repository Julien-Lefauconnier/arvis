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
    """Run the observation-only fusion for the gate stage.

    The signature is the stage's hook interface and stays wider than
    the fusion itself: ``delta_w`` feeds the stage's soft filter and
    ``global_safe`` the stability certificate, both upstream of this
    call; neither drives a fusion decision (audit G3 / D1 prune).
    ``ctx`` is accepted for hook compatibility and unused.
    """
    del delta_w, global_safe, ctx
    inputs = MultiaxialInputs(
        fast_verdict=pre_verdict,
        switching_safe=switching_safe,
    )
    return multiaxial_fusion(inputs)
