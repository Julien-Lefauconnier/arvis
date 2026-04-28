# arvis/kernel/pipeline/stages/conflict_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.conflict.conflict_extractor import extract_conflicts_from_bundle


class ConflictStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        bundle = ctx.bundle

        # -----------------------------------------
        # 1. Extract conflicts
        # -----------------------------------------
        conflicts = extract_conflicts_from_bundle(bundle)

        # -----------------------------------------
        # 2. Evaluate conflicts
        # -----------------------------------------
        ctx.conflict = pipeline.conflict_evaluator.apply(
            targets=[str(getattr(bundle, "bundle_id", "bundle"))],
            conflicts=conflicts,
        )

        # -----------------------------------------
        # 3. Compute conflict pressure
        # -----------------------------------------
        if "conflict_pressure" in ctx.extra:
            raw = ctx.extra["conflict_pressure"]

            if isinstance(raw, (int, float)):
                conflict_pressure = pipeline.conflict_pressure_engine.from_scalar(
                    float(raw)
                )
            else:
                conflict_pressure = raw
        else:
            has_conflicts = any(
                (getattr(c, "conflicts", None) and len(getattr(c, "conflicts", [])) > 0)
                or getattr(c, "active", False)
                or getattr(c, "score", 0.0) > 0.0
                for c in ctx.conflict
            )

            if not has_conflicts:
                conflict_pressure = pipeline.conflict_pressure_engine.compute([])
            else:
                conflict_pressure = pipeline.conflict_pressure_engine.compute(
                    ctx.conflict
                )

        ctx.conflict_pressure = conflict_pressure
