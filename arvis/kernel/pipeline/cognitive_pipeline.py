# arvis/kernel/pipeline/cognitive_pipeline.py

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any, Protocol

from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime
from arvis.ir.cognitive_ir import CognitiveIR
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.pipeline.cognitive_pipeline_result import CognitivePipelineResult
from arvis.kernel.pipeline.services.pipeline_bootstrap_service import (
    PipelineBootstrapService,
)
from arvis.kernel.pipeline.services.pipeline_finalize_service import (
    PipelineFinalizeService,
)
from arvis.kernel.pipeline.services.pipeline_input_service import (
    PipelineInputService,
)
from arvis.kernel.pipeline.services.pipeline_preparation_service import (
    PipelinePreparationService,
)
from arvis.kernel.pipeline.services.pipeline_replay_service import (
    PipelineReplayService,
)
from arvis.kernel.pipeline.services.pipeline_runner_service import (
    PipelineRunnerService,
)
from arvis.kernel.pipeline.services.pipeline_runtime_service import (
    PipelineRuntimeService,
)
from arvis.kernel.pipeline.services.pipeline_stage_registry_service import (
    PipelineStageRegistryService,
)
from arvis.telemetry.sink import NullTelemetrySink, TelemetrySink


class PipelineStage(Protocol):
    def run(
        self, pipeline: CognitivePipeline, ctx: CognitivePipelineContext
    ) -> None: ...


class CognitivePipeline:
    # runtime-wired attributes (set by PipelineBootstrapService)
    decision: Any
    bundle_builder: Any
    core: Any
    hysteresis: Any
    exploration: Any
    regime_policy: Any
    regime_estimator: Any
    epsilon_controller: Any
    temporal_pressure: Any
    temporal_regulation: Any
    action_policy: Any
    conflict_evaluator: Any
    observability: Any
    conflict_pressure_engine: Any
    coherence_observer: Any
    coherence_policy: Any
    control_runtimes: dict[str, CognitiveControlRuntime]

    tool_feedback_stage: PipelineStage
    tool_retry_stage: PipelineStage
    decision_stage: PipelineStage
    passive_stage: PipelineStage
    bundle_stage: PipelineStage
    conflict_stage: PipelineStage
    core_stage: PipelineStage
    regime_stage: PipelineStage
    temporal_stage: PipelineStage
    conflict_modulation_stage: PipelineStage
    control_stage: PipelineStage
    projection_stage: PipelineStage
    gate_stage: PipelineStage
    control_feedback_stage: PipelineStage
    structural_risk_stage: PipelineStage
    confirmation_stage: PipelineStage
    execution_stage: PipelineStage
    action_stage: PipelineStage
    intent_stage: PipelineStage
    runtime_stage: PipelineStage

    global_stability_observer: Any
    quadratic_lyapunov_family: Any
    quadratic_comparability: Any
    tool_executor: Any
    adaptive_kappa_estimator: Any
    pi_impl: Any
    pi_operator: Any
    projection_domain: Any
    projection_validator: Any

    def __init__(
        self,
        core_model: Any | None = None,
        *,
        strict_mode: bool = False,
    ) -> None:
        PipelineBootstrapService.run(
            self,
            core_model,
            strict_mode=strict_mode,
        )
        self.telemetry_sink: TelemetrySink = NullTelemetrySink()

    # -----------------------------------------------------
    # ITERATIVE PIPELINE SUPPORT (non-breaking)
    # -----------------------------------------------------
    def iter_stages(self) -> Iterable[PipelineStage]:
        """
        Ordered list of pipeline stages.
        Single source of truth for execution order.
        """
        return PipelineStageRegistryService.iter_stages(self)

    def _get_control_runtime(self, user_id: str) -> CognitiveControlRuntime:
        return PipelineRuntimeService.get_control_runtime(
            self,
            user_id,
        )

    def _prepare_run(
        self,
        ctx: CognitivePipelineContext,
    ) -> None:
        PipelinePreparationService.run(
            self,
            ctx,
        )

    def run_stage(
        self,
        ctx: CognitivePipelineContext,
        stage: PipelineStage,
    ) -> None:
        PipelineRunnerService.run_stage(
            self,
            ctx,
            stage,
        )

    # -----------------------------------------------------
    # PUBLIC API (safe wrapper)
    # -----------------------------------------------------
    def run_from_input(self, input_data: dict[str, Any]) -> CognitivePipelineResult:
        """
        Public entrypoint for external callers.
        Converts raw input into a pipeline context.
        """
        ctx = PipelineInputService.build_context(input_data)
        return self.run(ctx)

    def run(
        self,
        ctx: CognitivePipelineContext,
    ) -> CognitivePipelineResult:
        PipelineRunnerService.run_all(self, ctx)
        return self.finalize_run(ctx)

    def run_iter(
        self,
        ctx: CognitivePipelineContext,
    ) -> Iterator[PipelineStage]:
        yield from PipelineRunnerService.run_iter(
            self,
            ctx,
        )

    def finalize_run(self, ctx: CognitivePipelineContext) -> CognitivePipelineResult:
        return PipelineFinalizeService.run(
            self,
            ctx,
        )

    def run_from_ir(self, ir: CognitiveIR) -> CognitivePipelineResult:
        """
        Replay pipeline from canonical IR (deterministic mode).
        """
        ctx = PipelineReplayService.build_context(ir)
        return self.run(ctx)
