# arvis/kernel/pipeline/stages/regime_stage.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.math.switching.regime_mapper import map_regime

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class RegimeStage:
    def run(self, pipeline: CognitivePipeline, ctx: CognitivePipelineContext) -> None:
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
            except ImportError:
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
        except (TypeError, ValueError, OverflowError):
            theoretical_regime = None

        regime_ctx.theoretical_regime = theoretical_regime

        # -----------------------------------------
        # 1. Switching runtime ownership (campaign PROJ, P3)
        # -----------------------------------------
        # This stage no longer ticks the dwell clock. It used to call
        # switching_runtime.update() here, BEFORE the gate, while
        # runtime_stage called it again AFTER the gate on the same
        # object: two ticks per turn, so the guard read twice the real
        # dwell and ln(J)/tau_d was half its true value, declaring
        # switching safe with half the dwell actually served. The
        # single owner is runtime_stage, post-decision, so the guard
        # reads the dwell of COMPLETED turns (the conservative end).
