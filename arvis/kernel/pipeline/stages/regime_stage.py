# arvis/kernel/pipeline/stages/regime_stage.py

from __future__ import annotations

from typing import Any

from arvis.math.switching.regime_mapper import map_regime


class RegimeStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        scientific = getattr(ctx, "scientific", None)

        if scientific is not None:
            regime_ctx = scientific.regime_state
            switching_ctx = scientific.switching
        else:
            regime_ctx = None
            switching_ctx = None
        # -----------------------------------------
        # 0. Ensure switching runtime exists
        # -----------------------------------------
        runtime = (
            switching_ctx.switching_runtime
            if switching_ctx is not None
            else getattr(ctx, "switching_runtime", None)
        )

        if runtime is None:
            try:
                from arvis.math.switching.switching_runtime import SwitchingRuntime

                runtime = SwitchingRuntime()
            except Exception:
                runtime = None

        if switching_ctx is not None:
            switching_ctx.switching_runtime = runtime

        ctx.switching_runtime = runtime

        regime_snapshot = pipeline.regime_estimator.push(float(ctx.drift_score))

        if regime_snapshot:
            if regime_ctx is not None:
                regime_ctx.regime = regime_snapshot.regime
                regime_ctx.regime_confidence = regime_snapshot.confidence

            ctx.regime = regime_snapshot.regime
            ctx.regime_confidence = regime_snapshot.confidence
        else:
            if regime_ctx is not None:
                regime_ctx.regime = "transition"
                regime_ctx.regime_confidence = 0.0

            ctx.regime = "transition"
            ctx.regime_confidence = 0.0

        # -----------------------------------------
        # explicit regime q_t
        # -----------------------------------------
        try:
            theoretical_regime = map_regime(
                ctx.regime,
                ctx.regime_confidence,
            )

            if regime_ctx is not None:
                regime_ctx.theoretical_regime = theoretical_regime

            ctx.theoretical_regime = theoretical_regime
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
