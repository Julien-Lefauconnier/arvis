# arvis/kernel/pipeline/stages/runtime_stage.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.errors.boundaries.pipeline import (
    capture_pipeline_degraded_failure,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    scientific as scientific_of,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class RuntimeStage:
    def run(self, pipeline: CognitivePipeline, ctx: CognitivePipelineContext) -> None:
        try:
            runtime = ctx.runtime_bindings.control_runtime
            if runtime is None:
                getter = getattr(pipeline, "_get_control_runtime", None)
                if callable(getter):
                    runtime = getter(ctx.user_id)
                    ctx.runtime_bindings.control_runtime = runtime

            if runtime is not None:
                runtime.last_risk = float(ctx.scientific.core.collapse_risk)
                runtime.inertia_risk = float(ctx.scientific.core.collapse_risk)
                runtime.last_action = str(
                    getattr(ctx.execution.action_decision, "mode", None)
                )

        except Exception as exc:
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="RuntimeControlUpdate",
                message="Runtime control update failure",
            )

        # -----------------------------------------
        #  Switching runtime
        # -----------------------------------------
        try:
            switching_runtime = scientific_of(ctx).switching.switching_runtime
            regime = scientific_of(ctx).regime_state.regime

            if switching_runtime is not None and regime is not None:
                switching_runtime.update(str(regime))
        except Exception as exc:
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="RuntimeSwitchingUpdate",
                message="Runtime switching update failure",
            )

        # -----------------------------------------
        # Global stability observer
        # -----------------------------------------
        try:
            observer = getattr(pipeline, "global_stability_observer", None)
            if observer:
                metrics = observer.update(ctx)
                scientific_of(ctx).adaptive.global_stability_metrics = metrics
        except Exception as exc:
            scientific_of(ctx).adaptive.global_stability_metrics = None
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="GlobalStabilityObserver",
                message="Runtime observer update failure",
            )
