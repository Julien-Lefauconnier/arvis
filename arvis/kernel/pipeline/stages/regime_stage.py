# arvis/kernel/pipeline/stages/regime_stage.py

from __future__ import annotations

from typing import Any

from arvis.math.switching.regime_mapper import map_regime


class RegimeStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        # -----------------------------------------
        # 0. Ensure switching runtime exists
        # -----------------------------------------
        if getattr(ctx, "switching_runtime", None) is None:
            try:
                from arvis.math.switching.switching_runtime import SwitchingRuntime

                ctx.switching_runtime = SwitchingRuntime()
            except Exception:
                ctx.switching_runtime = None

        regime_snapshot = pipeline.regime_estimator.push(float(ctx.drift_score))

        if regime_snapshot:
            ctx.regime = regime_snapshot.regime
            ctx.regime_confidence = regime_snapshot.confidence
        else:
            ctx.regime = "transition"
            ctx.regime_confidence = 0.0

        # -----------------------------------------
        # explicit regime q_t
        # -----------------------------------------
        try:
            ctx.theoretical_regime = map_regime(
                ctx.regime,
                ctx.regime_confidence,
            )
        except Exception:
            ctx.theoretical_regime = None

        # -----------------------------------------
        # 1. Update switching runtime
        # -----------------------------------------
        if ctx.switching_runtime is not None and ctx.regime is not None:
            try:
                ctx.switching_runtime.update(ctx.regime)
            except Exception:
                pass
