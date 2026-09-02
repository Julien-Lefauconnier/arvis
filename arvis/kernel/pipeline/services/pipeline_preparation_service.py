# arvis/kernel/pipeline/services/pipeline_preparation_service.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.kernel.execution.cognitive_execution_state import CognitiveExecutionState
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.services.pipeline_ir_bootstrap_service import (
    PipelineIRBootstrapService,
)
from arvis.kernel.projection.certificate import minimal_projection_certificate
from arvis.math.switching.switching_params import (
    SwitchingParams,
)
from arvis.math.switching.switching_runtime import (
    SwitchingRuntime,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
    )


class PipelinePreparationService:
    """
    Runtime-safe pipeline bootstrap service.

    Responsibilities:
    - bootstrap canonical IR inputs/context
    - initialize runtime-owned state
    - initialize switching runtime state
    - prepare deterministic execution context

    Preparation MUST occur once per pipeline lifecycle.
    """

    DEFAULT_SWITCHING_PARAMS = SwitchingParams(
        alpha=0.15,
        gamma_z=0.4,
        eta=0.05,
        L_T=1.0,
        J=1.5,
    )

    @staticmethod
    def run(
        pipeline: CognitivePipeline,
        ctx: CognitivePipelineContext,
    ) -> None:
        # -----------------------------------------
        # Idempotent lifecycle guard
        # -----------------------------------------
        # Typed latch (LOT O3); the extra key below is a write-only
        # export, so a host-seeded key cannot skip preparation.
        if ctx._pipeline_prepared:
            return

        # -----------------------------------------
        # Canonical IR bootstrap
        # -----------------------------------------
        PipelineIRBootstrapService.bootstrap_input(ctx)
        PipelineIRBootstrapService.bootstrap_context(ctx)

        # -----------------------------------------
        # Runtime execution bootstrap
        # -----------------------------------------
        if ctx.execution.execution_state is None:
            ctx.execution.execution_state = CognitiveExecutionState()

        # -----------------------------------------
        # Switching runtime bootstrap
        # -----------------------------------------
        switching = ctx.scientific.switching
        if switching.switching_params is None:
            switching.switching_params = (
                PipelinePreparationService.DEFAULT_SWITCHING_PARAMS
            )

        if switching.switching_runtime is None:
            # A fresh clock by default. When the host threads the
            # opaque blob, core_stage (the single ingestion point of
            # extra["scientific_state"]) restores the previous turn's
            # clock over this one (campaign PROJ, P3).
            switching.switching_runtime = SwitchingRuntime()

        # -----------------------------------------
        # Quadratic comparability projection
        # -----------------------------------------
        comp = getattr(
            pipeline,
            "quadratic_comparability",
            None,
        )

        if comp is not None and switching.switching_params is not None:
            p = switching.switching_params

            switching.switching_params = SwitchingParams(
                alpha=float(p.alpha),
                gamma_z=float(p.gamma_z),
                eta=float(p.eta),
                L_T=float(p.L_T),
                J=float(comp.J),
            )

        # -----------------------------------------
        # Minimal projection for bare informational inputs
        # -----------------------------------------
        # A plain-text prompt carries no structured signals to project. Attach a
        # minimal certificate so the turn is governed by the gate rather than
        # hard-blocked on an empty projection.
        cognitive_input = getattr(ctx, "cognitive_input", None)
        if isinstance(cognitive_input, str) and ctx.projection.certificate is None:
            cert = minimal_projection_certificate()
            ctx.projection.certificate = cert
            ctx.projection.domain_valid = cert.domain_valid
            ctx.projection.margin = cert.margin_to_boundary

        # -----------------------------------------
        # Lifecycle prepared marker
        # -----------------------------------------
        ctx._pipeline_prepared = True
        ctx.extra["__pipeline_prepared"] = True
