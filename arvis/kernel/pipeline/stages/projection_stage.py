# arvis/kernel/pipeline/stages/projection_stage.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from arvis.errors.boundaries.pipeline import (
    capture_pipeline_runtime_failure,
)
from arvis.kernel.pipeline.context.journal_context import journal_of
from arvis.math.projection.projection_view import ProjectionView

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class ProjectionStage:
    """
    Canonical projection stage.

    Responsibilities:
    - Run Π_impl (runtime projection)
    - Build projection_view
    - Run certification (Π_cert)
    """

    def run(self, pipeline: CognitivePipeline, ctx: CognitivePipelineContext) -> None:
        self._compute_projection(pipeline, ctx)

    def refresh(self, pipeline: Any, ctx: Any) -> None:
        """Post-hoc attestation (campaign PROJ, DM-P2).

        This used to run the full projection again during finalize and
        overwrite every decision field, certificate included, so the
        published certificate was not the one the gate consumed: on the
        smoke corpus the two differed on 42 turns of 42, materially on
        18 (LOCAL at decision time, BASIC in the trace). The refresh
        now RE-VALIDATES THE DECISION'S OWN VIEW against the signals
        that only exist after the gate (the composite energy delta, so
        the Lyapunov axis is finally assessed for real) and publishes
        the result under distinct names. What decided stays untouched;
        what is known after the fact is reported next to it.
        """
        try:
            view = ctx.projection.view
            if view is None or ctx.projection.certificate is None:
                return

            previous_projected: dict[str, float] | None = (
                pipeline.pi_impl.project_previous(ctx)
            )
            if hasattr(pipeline, "pi_operator") and previous_projected:
                previous_projected = pipeline.pi_operator.project(
                    ProjectionView.from_mapping(previous_projected),
                    ctx,
                )

            try:
                post_certificate = pipeline.projection_validator.validate(
                    view,
                    previous_projected=previous_projected,
                    ctx=ctx,
                )
            except TypeError:
                post_certificate = pipeline.projection_validator.validate(
                    view,
                    previous_projected=previous_projected,
                )

            ctx.projection.post_certificate = post_certificate
            ctx.extra["projection_post_certification_level"] = (
                post_certificate.certification_level.value
            )
            ctx.extra["projection_post_lyapunov_compatible"] = bool(
                post_certificate.lyapunov_compatibility_ok
            )
        except Exception as exc:
            capture_pipeline_runtime_failure(
                ctx,
                exc,
                component="ProjectionStage",
                message="Projection post-hoc attestation failure",
            )
            raise

    def _compute_projection(
        self,
        pipeline: Any,
        ctx: Any,
    ) -> None:
        try:
            # -----------------------------------------
            # Skip if already computed (pre-gate)
            # -----------------------------------------
            if ctx.projection.certificate is not None:
                return

            # -----------------------------------------
            # Structured Π (intermediate/full-theory path)
            # -----------------------------------------
            pi_state = None
            if hasattr(pipeline.pi_impl, "project_structured"):
                pi_state = pipeline.pi_impl.project_structured(ctx)
                ctx.projection.structured_projection = pi_state
                if (journal := journal_of(ctx)) is not None:
                    journal.pi_structured_available = True
                ctx.extra["pi_structured_available"] = True
                ctx.extra["projection_structured"] = True
            else:
                ctx.projection.structured_projection = None
                if (journal := journal_of(ctx)) is not None:
                    journal.pi_structured_available = False
                ctx.extra["pi_structured_available"] = False
                ctx.extra["projection_structured"] = False

            # -----------------------------------------
            # Π_impl
            # -----------------------------------------
            projected_state = pipeline.pi_impl.project(ctx)
            projection_view = projected_state.to_projection_view()

            # -----------------------------------------
            # SAFETY FALLBACK (kernel invariant)
            # -----------------------------------------
            if len(projection_view) == 0:
                projection_view = ProjectionView.from_mapping(
                    {"state.system_tension": 0.0}
                )

            if not isinstance(projection_view, ProjectionView):
                projection_view = ProjectionView.from_mapping(projection_view)

            # -----------------------------------------
            # RAW SNAPSHOT (observability)
            # -----------------------------------------
            projection_view_raw = projection_view.to_dict()

            # -----------------------------------------
            # Π_op (optional)
            # -----------------------------------------
            if hasattr(pipeline, "pi_operator"):
                projection_view = pipeline.pi_operator.project(
                    projection_view,
                    ctx,
                )

            # -----------------------------------------
            # Previous projection (for Lipschitz)
            # -----------------------------------------
            previous_projected: dict[str, float] | None = (
                pipeline.pi_impl.project_previous(ctx)
            )

            if hasattr(pipeline, "pi_operator") and previous_projected:
                previous_projected = pipeline.pi_operator.project(
                    ProjectionView.from_mapping(previous_projected),
                    ctx,
                )

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
            ctx.projection.runtime_projection = projected_state
            ctx.projection.view = projection_view
            ctx.projection.view_raw = projection_view_raw

            ctx.projection.certificate = projection_certificate
            ctx.projection.domain_valid = projection_certificate.domain_valid
            ctx.projection.margin = projection_certificate.margin_to_boundary

            ctx.extra["projection_certification_level"] = (
                projection_certificate.certification_level.value
            )
            ctx.extra["projection_source"] = "PiImpl"

            if (journal := journal_of(ctx)) is not None:
                structured = journal.pi_structured_available
            else:
                structured = bool(ctx.extra.get("pi_structured_available"))
            ctx.extra["projection_semantics"] = (
                "structured+certified" if structured else "flat+certified"
            )

        except Exception as exc:
            capture_pipeline_runtime_failure(
                ctx,
                exc,
                component="ProjectionStage",
                message="Projection stage failure",
            )
            raise
