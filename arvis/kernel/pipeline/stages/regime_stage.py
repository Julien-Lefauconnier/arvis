# arvis/kernel/pipeline/stages/regime_stage.py

from __future__ import annotations

from typing import Any

class RegimeStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        regime_snapshot = pipeline.regime_estimator.push(
            float(ctx.drift_score)
        )

        if regime_snapshot:
            ctx.regime = regime_snapshot.regime
            ctx.regime_confidence = regime_snapshot.confidence
        else:
            ctx.regime = "transition"
            ctx.regime_confidence = 0.0