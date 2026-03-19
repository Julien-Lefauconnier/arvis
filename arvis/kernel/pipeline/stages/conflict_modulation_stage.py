# arvis/kernel/pipeline/stages/conflict_modulation_stage.py

from __future__ import annotations

from typing import Any
from arvis.math.signals import RiskSignal
from arvis.cognition.conflict.conflict_modulation import apply_conflict_to_risk


class ConflictModulationStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        conflict_pressure = getattr(ctx, "conflict_pressure", None)

        if conflict_pressure is None:
            conflict_pressure = pipeline.conflict_pressure_engine.compute([])

        pressure_value = conflict_pressure.global_score

        adjusted_risk = apply_conflict_to_risk(
            base_risk=float(ctx.collapse_risk),
            conflict_pressure=pressure_value,
        )

        ctx.collapse_risk = RiskSignal(adjusted_risk)

        # expose for downstream stages
        ctx.conflict_pressure = conflict_pressure