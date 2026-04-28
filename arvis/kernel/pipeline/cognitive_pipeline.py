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
from arvis.kernel.pipeline.services.pipeline_compatibility_service import (
    PipelineCompatibilityService,
)
from arvis.kernel.pipeline.services.pipeline_execution_service import (
    PipelineExecutionService,
)
from arvis.kernel.pipeline.services.pipeline_execution_sync_service import (
    PipelineExecutionSyncService,
)
from arvis.kernel.pipeline.services.pipeline_iteration_service import (
    PipelineIterationService,
)
from arvis.kernel.pipeline.services.pipeline_lifecycle_service import (
    PipelineLifecycleService,
)
from arvis.kernel.pipeline.services.pipeline_preparation_service import (
    PipelinePreparationService,
)
from arvis.kernel.pipeline.services.pipeline_runtime_service import (
    PipelineRuntimeService,
)
from arvis.kernel.pipeline.services.pipeline_stage_execution_service import (
    PipelineStageExecutionService,
)
from arvis.kernel.pipeline.services.pipeline_stage_registry_service import (
    PipelineStageRegistryService,
)
from arvis.math.switching.switching_params import SwitchingParams

DEFAULT_SWITCHING_PARAMS = SwitchingParams(
    alpha=0.15,
    gamma_z=0.4,
    eta=0.05,
    L_T=1.0,
    J=1.5,
)


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

    def __init__(self, core_model: Any | None = None) -> None:
        PipelineBootstrapService.run(
            self,
            core_model,
        )

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

    # -----------------------------------------------------
    # COMPATIBILITY WRAPPERS
    # Legacy internal API preserved while delegating to
    # service layer. Some runtime/tests still call these.
    # -----------------------------------------------------
    def _safe_run(
        self,
        stage: PipelineStage,
        ctx: CognitivePipelineContext,
    ) -> None:
        PipelineCompatibilityService.safe_run(
            self,
            stage,
            ctx,
        )

    def _bootstrap_ir_input(
        self,
        ctx: CognitivePipelineContext,
    ) -> None:
        PipelineCompatibilityService.bootstrap_ir_input(ctx)

    def _bootstrap_ir_context(
        self,
        ctx: CognitivePipelineContext,
    ) -> None:
        PipelineCompatibilityService.bootstrap_ir_context(ctx)

    def _refresh_ir_context_extra(
        self,
        ctx: CognitivePipelineContext,
    ) -> None:
        PipelineCompatibilityService.refresh_ir_context_extra(ctx)

    def _prepare_run(
        self,
        ctx: CognitivePipelineContext,
    ) -> None:
        PipelinePreparationService.run(
            self,
            ctx,
        )

    def _sync_execution_flags(
        self,
        ctx: CognitivePipelineContext,
    ) -> None:
        PipelineExecutionSyncService.run(ctx)

    def run_stage(
        self,
        ctx: CognitivePipelineContext,
        stage: PipelineStage,
    ) -> None:
        PipelineStageExecutionService.run_stage(
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
        return PipelineLifecycleService.run_from_input(
            self,
            input_data,
        )

    def run(
        self,
        ctx: CognitivePipelineContext,
    ) -> CognitivePipelineResult:
        return PipelineExecutionService.run(
            self,
            ctx,
        )

    def run_iter(
        self,
        ctx: CognitivePipelineContext,
    ) -> Iterator[PipelineStage]:
        yield from PipelineIterationService.run_iter(
            self,
            ctx,
        )

    def finalize_run(self, ctx: CognitivePipelineContext) -> CognitivePipelineResult:
        return PipelineLifecycleService.finalize(
            self,
            ctx,
        )

    def run_from_ir(self, ir: CognitiveIR) -> CognitivePipelineResult:
        """
        Replay pipeline from canonical IR (deterministic mode).
        """
        return PipelineLifecycleService.run_from_ir(
            self,
            ir,
        )
