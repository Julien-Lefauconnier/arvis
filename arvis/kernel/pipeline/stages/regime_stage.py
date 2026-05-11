# arvis/kernel/pipeline/stages/regime_stage.py

from __future__ import annotations

from typing import Any

from arvis.math.switching.regime_mapper import map_regime


class RegimeStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        scientific = ctx.scientific
        regime_ctx = scientific.regime_state
        switching_ctx = scientific.switching
        # -----------------------------------------
        # 0. Ensure switching runtime exists
        # -----------------------------------------
        runtime = switching_ctx.switching_runtime

        if runtime is None:
            try:
                from arvis.math.switching.switching_runtime import SwitchingRuntime

                runtime = SwitchingRuntime()
            except Exception:
                runtime = None

        if switching_ctx is not None:
            switching_ctx.switching_runtime = runtime

        regime_snapshot = pipeline.regime_estimator.push(
            float(scientific.core.drift_score)
        )

        if regime_snapshot:
            regime_ctx.regime = regime_snapshot.regime
            regime_ctx.regime_confidence = regime_snapshot.confidence
        else:
            regime_ctx.regime = "transition"
            regime_ctx.regime_confidence = 0.0

        # -----------------------------------------
        # explicit regime q_t
        # -----------------------------------------
        try:
            theoretical_regime = map_regime(
                regime_ctx.regime,
                regime_ctx.regime_confidence,
            )
        except Exception:
            theoretical_regime = None

        regime_ctx.theoretical_regime = theoretical_regime

        # -----------------------------------------
        # 1. Update switching runtime
        # -----------------------------------------
        if (
            switching_ctx.switching_runtime is not None
            and regime_ctx.regime is not None
        ):
            try:
                switching_ctx.switching_runtime.update(regime_ctx.regime)
            except Exception:
                pass
