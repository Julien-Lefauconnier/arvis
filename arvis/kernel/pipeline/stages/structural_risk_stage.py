# arvis/kernel/pipeline/stages/structural_risk_stage.py

from __future__ import annotations

from typing import Any
import numpy as np


class StructuralRiskStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        prev_slow = getattr(ctx, "slow_state_prev", None)
        cur_slow = getattr(ctx, "slow_state", None)

        slow_divergence = None

        if prev_slow is not None and cur_slow is not None:
            try:
                dz = cur_slow.as_vector() - prev_slow.as_vector()
                slow_divergence = float(np.dot(dz, dz))
            except Exception:
                slow_divergence = None

        # -----------------------------------------
        # EXPORT (observability only)
        # -----------------------------------------
        ctx.slow_divergence = slow_divergence

        # -----------------------------------------
        # STRUCTURAL RISK FLAG (non-math layer)
        # -----------------------------------------
        if slow_divergence is not None and slow_divergence > 0.05:
            ctx.extra["structural_risk"] = True
        else:
            ctx.extra["structural_risk"] = False
