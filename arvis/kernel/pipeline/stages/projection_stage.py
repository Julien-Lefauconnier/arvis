# arvis/kernel/pipeline/stages/projection_stage.py

from __future__ import annotations

from typing import Any, Dict, Optional


class ProjectionStage:
    """
    Canonical projection stage.

    Responsibilities:
    - Run Π_impl (runtime projection)
    - Build projection_view
    - Run certification (Π_cert)
    """

    def run(self, pipeline: Any, ctx: Any) -> None:
        self._compute_projection(pipeline, ctx, allow_overwrite=False)

    def refresh(self, pipeline: Any, ctx: Any) -> None:
        self._compute_projection(pipeline, ctx, allow_overwrite=True)

    def _compute_projection(
        self,
        pipeline: Any,
        ctx: Any,
        allow_overwrite: bool = False,
    ) -> None:
        try:
            # -----------------------------------------
            # Skip if already computed (pre-gate)
            # -----------------------------------------
            if ctx.projection_certificate is not None and not allow_overwrite:
                return
            
            # -----------------------------------------
            # Structured Π (intermediate/full-theory path)
            # -----------------------------------------
            pi_state = None
            if hasattr(pipeline.pi_impl, "project_structured"):
                pi_state = pipeline.pi_impl.project_structured(ctx)
                ctx.pi_state = pi_state
                ctx.extra["pi_structured_available"] = True
                ctx.extra["projection_structured"] = True
            else:
                ctx.pi_state = None
                ctx.extra["pi_structured_available"] = False
                ctx.extra["projection_structured"] = False

            # -----------------------------------------
            # Π_impl
            # -----------------------------------------
            projected_state = pipeline.pi_impl.project(ctx)
            projection_view: Dict[str, float] = projected_state.to_projection_view()

            # -----------------------------------------
            # SAFETY FALLBACK (kernel invariant)
            # -----------------------------------------
            if not projection_view:
                projection_view = {"state.system_tension": 0.0}

            # -----------------------------------------
            # RAW SNAPSHOT (observability)
            # -----------------------------------------
            projection_view_raw: Dict[str, float] = dict(projection_view)

            # -----------------------------------------
            # Π_op (optional)
            # -----------------------------------------
            if hasattr(pipeline, "pi_operator"):
                projection_view = pipeline.pi_operator.project(projection_view, ctx)

            # -----------------------------------------
            # Previous projection (for Lipschitz)
            # -----------------------------------------
            previous_projected: Optional[Dict[str, float]] = (
                pipeline.pi_impl.project_previous(ctx)
            )

            if hasattr(pipeline, "pi_operator") and previous_projected:
               previous_projected = pipeline.pi_operator.project(previous_projected, ctx)

            # -----------------------------------------
            # Π_cert
            # -----------------------------------------
            try:
                projection_certificate = pipeline.projection_validator.validate(
                    projection_view,
                    previous_projected=previous_projected,
                    ctx=ctx,
                )
            except TypeError:
                projection_certificate = pipeline.projection_validator.validate(
                    projection_view,
                    previous_projected=previous_projected,
                )

            # -----------------------------------------
            # Persist in context
            # -----------------------------------------
            ctx.projected_state = projected_state
            ctx.projection_view = projection_view
            ctx.projection_view_raw = projection_view_raw

            ctx.projection_certificate = projection_certificate
            ctx.projection_domain_valid = projection_certificate.domain_valid
            ctx.projection_margin = projection_certificate.margin_to_boundary

            ctx.extra["projection_certification_level"] = (
                projection_certificate.certification_level.value
            )
            ctx.extra["projection_source"] = "PiImpl"

            ctx.extra["projection_semantics"] = (
                "structured+certified"
                if ctx.extra.get("pi_structured_available")
                else "flat+certified"
            )

        except Exception:
            ctx.extra.setdefault("errors", []).append("projection_stage_failure")
            raise