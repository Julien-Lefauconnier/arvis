# arvis/kernel/pipeline/services/pipeline_preparation_service.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.math.switching.switching_runtime import (
    SwitchingRuntime,
)
from arvis.math.switching.switching_params import (
    SwitchingParams,
)


from arvis.kernel.pipeline.services.pipeline_ir_bootstrap_service import (
    PipelineIRBootstrapService,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
    )


class PipelinePreparationService:
    DEFAULT_SWITCHING_PARAMS = SwitchingParams(
        alpha=0.15,
        gamma_z=0.4,
        eta=0.05,
        L_T=1.0,
        J=1.5,
    )
    @staticmethod
    def run(
        pipeline: "CognitivePipeline",
        ctx: CognitivePipelineContext,
    ) -> None:
        if ctx.extra.get(
            "__pipeline_prepared",
            False,
        ):
            return

        PipelineIRBootstrapService.bootstrap_input(
            ctx
        )
        PipelineIRBootstrapService.bootstrap_context(
            ctx
        )

        if getattr(
            ctx,
            "switching_params",
            None,
        ) is None:
            ctx.switching_params = (
                PipelinePreparationService
                .DEFAULT_SWITCHING_PARAMS
            )
        if getattr(
            ctx,
            "switching_runtime",
            None,
        ) is None:
            ctx.switching_runtime = (
                SwitchingRuntime()
            )

        try:
            comp = getattr(
                pipeline,
                "quadratic_comparability",
                None,
            )

            if (
                comp is not None
                and getattr(
                    ctx,
                    "switching_params",
                    None,
                )
                is not None
            ):
                p = ctx.switching_params

                if p is None:
                    p = (
                    PipelinePreparationService
                    .DEFAULT_SWITCHING_PARAMS
                )

                ctx.switching_params = (
                    SwitchingParams(
                        alpha=float(
                            p.alpha
                        ),
                        gamma_z=float(
                            p.gamma_z
                        ),
                        eta=float(
                            p.eta
                        ),
                        L_T=float(
                            p.L_T
                        ),
                        J=float(
                            comp.J
                        ),
                    )
                )
        except Exception:
            pass

        ctx.extra[
            "__pipeline_prepared"
        ] = True