# arvis/kernel/pipeline/stages/core_stage.py

from __future__ import annotations

from typing import Any, Optional
from arvis.math.signals import RiskSignal, DriftSignal
from arvis.math.lyapunov.lyapunov import LyapunovState


class CoreStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        bundle = ctx.bundle

        # -----------------------------------------
        # 1. Core processing
        # -----------------------------------------
        scientific = pipeline.core.process(bundle)
        ctx.scientific_snapshot = scientific

        core_snapshot = getattr(scientific, "core_snapshot", None) or scientific

        # -----------------------------------------
        # 2. Collapse risk
        # -----------------------------------------
        ctx.collapse_risk = RiskSignal(
            getattr(scientific, "collapse_risk", 0.0) or 0.0
        )

        # -----------------------------------------
        # 3. Lyapunov states
        # -----------------------------------------
        ctx.prev_lyap = (
            getattr(scientific, "prev_lyap", None)
            or getattr(core_snapshot, "prev_lyap", None)
        )

        ctx.cur_lyap = (
            getattr(scientific, "cur_lyap", None)
            or getattr(core_snapshot, "cur_lyap", None)
        )

        def _normalize_lyap(x: Any) -> Optional[LyapunovState]:
            if x is None:
                return None
            if isinstance(x, LyapunovState):
                return x
            return LyapunovState.from_scalar(x)

        ctx.prev_lyap = _normalize_lyap(ctx.prev_lyap)
        ctx.cur_lyap = _normalize_lyap(ctx.cur_lyap)

        # -----------------------------------------
        # 4. Drift
        # -----------------------------------------
        ctx.drift_score = DriftSignal(
            getattr(scientific, "drift_score", None)
            or getattr(scientific, "dv", None)
            or getattr(core_snapshot, "drift_score", None)
            or getattr(core_snapshot, "dv", 0.0)
            or 0.0
        )

        # -----------------------------------------
        # 5. Regime + stability
        # -----------------------------------------
        ctx.regime = (
            getattr(scientific, "regime", None)
            or getattr(core_snapshot, "regime", None)
        )

        ctx.stable = (
            getattr(scientific, "stable", None)
            if getattr(scientific, "stable", None) is not None
            else getattr(core_snapshot, "stable", None)
        )