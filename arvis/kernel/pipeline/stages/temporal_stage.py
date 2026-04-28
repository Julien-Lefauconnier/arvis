# arvis/kernel/pipeline/stages/temporal_stage.py

from __future__ import annotations

from typing import Any

from arvis.math.signals import RiskSignal


class TemporalStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        timeline = ctx.timeline or []
        total = len(timeline)

        # -----------------------------------------
        # 1. timeline parsing helpers
        # -----------------------------------------
        def _timeline_text(entry: Any) -> str:
            if isinstance(entry, dict):
                parts = [
                    entry.get("type", ""),
                    entry.get("title", ""),
                    entry.get("description", ""),
                ]
            else:
                parts = [
                    getattr(entry, "type", ""),
                    getattr(entry, "title", ""),
                    getattr(entry, "description", ""),
                ]
            return " ".join(str(p) for p in parts if p).lower()

        has_conflicts = any("conflict" in _timeline_text(e) for e in timeline)
        has_gaps = any("gap" in _timeline_text(e) for e in timeline)
        has_uncertainty = any("uncertainty" in _timeline_text(e) for e in timeline)

        healthy = True  # kernel-only

        # -----------------------------------------
        # 2. compute pressure + modulation
        # -----------------------------------------
        temporal_pressure = pipeline.temporal_pressure.compute(
            total=total,
            has_conflicts=has_conflicts,
            has_gaps=has_gaps,
            has_uncertainty=has_uncertainty,
            healthy=healthy,
        )

        temporal_modulation = pipeline.temporal_regulation.compute(
            total=total,
            has_conflicts=has_conflicts,
            has_gaps=has_gaps,
            has_uncertainty=has_uncertainty,
            healthy=healthy,
        )

        # -----------------------------------------
        # 3. apply modulation
        # -----------------------------------------
        adjusted_risk = float(ctx.collapse_risk) * temporal_modulation.risk_multiplier
        ctx.collapse_risk = RiskSignal(adjusted_risk)

        # -----------------------------------------
        # 4. expose
        # -----------------------------------------
        ctx.temporal_pressure = temporal_pressure
        ctx.temporal_modulation = temporal_modulation
