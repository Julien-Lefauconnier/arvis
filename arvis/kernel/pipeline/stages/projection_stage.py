# arvis/kernel/pipeline/stages/projection_stage.py

from __future__ import annotations

from typing import Any, Dict


class ProjectionStage:
    """
    Canonical projection stage.

    Responsibilities:
    - Build minimal projection (pre-gate safety)
    - Refresh projection after observability (full signal space)
    """

    def run(self, pipeline: Any, ctx: Any) -> None:
        self._compute_projection(pipeline, ctx, allow_overwrite=False)

    # -----------------------------------------
    # PUBLIC: post-observability refresh
    # -----------------------------------------
    def refresh(self, pipeline: Any, ctx: Any) -> None:
        self._compute_projection(pipeline, ctx, allow_overwrite=True)

    # -----------------------------------------
    # INTERNAL
    # -----------------------------------------
    def _compute_projection(
        self,
        pipeline: Any,
        ctx: Any,
        allow_overwrite: bool = False,
    ) -> None:
        try:
            projection_view: Dict[str, float] = {}

            system_tension = getattr(ctx, "system_tension", None)

            if isinstance(system_tension, (int, float)):
                projection_view["system_tension"] = float(system_tension)

            # -----------------------------------------
            # SAFETY FALLBACK
            # Projection must always exist (kernel invariant)
            # -----------------------------------------
            if not projection_view:
                projection_view["system_tension"] = 0.0

            if ctx.projection_certificate is not None and not allow_overwrite:
                return

            projection_certificate = pipeline.projection_validator.validate(
                projection_view,
                previous_projected=None,
            )

            ctx.projection_certificate = projection_certificate
            ctx.projection_domain_valid = projection_certificate.domain_valid
            ctx.projection_margin = projection_certificate.margin_to_boundary

            ctx.extra["projection_certification_level"] = (
                projection_certificate.certification_level.value
            )

        except Exception:
            ctx.extra.setdefault("errors", []).append("projection_stage_failure")