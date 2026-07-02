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
        if ctx.extra.get("__pipeline_prepared", False):
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
        if ctx.switching_params is None:
            ctx.switching_params = PipelinePreparationService.DEFAULT_SWITCHING_PARAMS

        if ctx.switching_runtime is None:
            ctx.switching_runtime = SwitchingRuntime()

        # -----------------------------------------
        # Quadratic comparability projection
        # -----------------------------------------
        comp = getattr(
            pipeline,
            "quadratic_comparability",
            None,
        )

        if comp is not None and ctx.switching_params is not None:
            p = ctx.switching_params

            ctx.switching_params = SwitchingParams(
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
            ctx.projection_certificate = cert
            ctx.projection.domain_valid = cert.domain_valid
            ctx.projection.margin = cert.margin_to_boundary

        # -----------------------------------------
        # Lifecycle prepared marker
        # -----------------------------------------
        ctx.extra["__pipeline_prepared"] = True
