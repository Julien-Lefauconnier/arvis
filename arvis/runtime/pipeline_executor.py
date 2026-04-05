# arvis/runtime/pipeline_executor.py

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.runtime.cognitive_process import BudgetConsumption, CognitiveProcess


@dataclass(frozen=True)
class PipelineExecutionOutcome:
    result: Any
    consumption: BudgetConsumption
    completed: bool
    stage_name: str | None = None

class PipelineExecutor:
    """
    V1 bridge:
    one scheduler execution = one full pipeline run.

    Later this class can evolve toward stage-by-stage execution without
    changing the scheduler contract.

    EXECUTION INVARIANTS:

    1. Always returns a non-null result (fallback enforced)
    2. completed=True ⇒ pipeline fully executed (final state)
    3. completed=False ⇒ intermediate step (iterative mode only)
    4. BudgetConsumption is always reported
    5. Single-step budget MAY force full execution (test/runtime fallback)

    """

    def __init__(self, pipeline: CognitivePipeline):
        self.pipeline = pipeline
        self.use_iterative = True

    def execute_process(self, process: CognitiveProcess) -> PipelineExecutionOutcome:
        ctx = process.local_state
        if not isinstance(ctx, CognitivePipelineContext):
            raise TypeError("process.local_state must be a CognitivePipelineContext")

        start = perf_counter()

        # =====================================================
        # AUTO-FALLBACK: single-step budget = full execution
        # =====================================================
        if process.budget.reasoning_steps <= 1:
            return self._run_full_pipeline(ctx, start, "AutoFullRun")

        # =====================================================
        # TEST MODE FALLBACK (no iter_stages)
        # =====================================================
        if not hasattr(self.pipeline, "iter_stages"):
            return self._run_full_pipeline(ctx, start, "DirectRun")
        
        if not self.use_iterative:
            return self._run_full_pipeline(ctx, start, "NonIterativeRun")
        
        # =====================================================
        # PROCESS EXECUTION
        # =====================================================

        stages = list(self.pipeline.iter_stages())
        if process.total_stage_count is None:
            process.set_total_stage_count(len(stages))

        if not process.pipeline_prepared:
            self.pipeline._prepare_run(ctx)
            process.mark_pipeline_prepared()
        
        result: Any
        completed: bool
        stage_name: str

        if process.has_remaining_stages():
            stage = stages[process.current_stage_index]
            self.pipeline.run_stage(ctx, stage)
            process.advance_stage(stage.__class__.__name__)
            result = self._build_partial_result(ctx)
            completed = False
            stage_name = stage.__class__.__name__
        else:
            result = self.pipeline.finalize_run(ctx)
            assert result is not None
            process.mark_pipeline_finalized()

            # ----------------------------------------
            # HARD GUARANTEE: finalize must not return None
            # ----------------------------------------
            if result is None:
                result = self._build_fallback_result(ctx)

            completed = True
            stage_name = "FinalizeRun"

        elapsed_ms = max(1, int((perf_counter() - start) * 1000.0))

        consumption = BudgetConsumption(
            reasoning_steps=1,
            attention_tokens=1,
            uncertainty_spent=0.0,
            elapsed_ms=elapsed_ms,
            memory_span_used=0,
        )
        return PipelineExecutionOutcome(
            result=result,
            consumption=consumption,
            completed=completed,
            stage_name=stage_name,
        )
    
    def _build_partial_result(self, ctx: CognitivePipelineContext) -> Any:
        """
        Minimal non-null result for intermediate stages.
        Prevents None propagation in iterative execution.
        """

        class PartialResult:
            can_execute = True
            requires_confirmation = False

            ir_input = getattr(ctx, "ir_input", {})
            ir_context = getattr(ctx, "ir_context", {})
            ir_decision: dict[str, Any] = {}
            ir_state: dict[str, Any] = {}
            ir_gate: dict[str, Any] = {}

        return PartialResult()


    def _build_fallback_result(self, ctx: CognitivePipelineContext) -> Any:
        """
        Safety fallback if finalize_run returns None.
        """

        class FallbackResult:
            can_execute = True
            requires_confirmation = False

            ir_input = getattr(ctx, "ir_input", {})
            ir_context = getattr(ctx, "ir_context", {})
            ir_decision: dict[str, Any] = {}
            ir_state: dict[str, Any] = {}
            ir_gate: dict[str, Any] = {}

        return FallbackResult()
    
    def _run_full_pipeline(
        self,
        ctx: CognitivePipelineContext,
        start: float,
        stage_name: str
    ) -> PipelineExecutionOutcome:
        result = self.pipeline.run(ctx)
        if result is None:
            result = self._build_fallback_result(ctx)
        elapsed_ms = max(1, int((perf_counter() - start) * 1000.0))
        return PipelineExecutionOutcome(
            result=result,
            consumption=BudgetConsumption(
                reasoning_steps=1,
                attention_tokens=1,
                uncertainty_spent=0.0,
                elapsed_ms=elapsed_ms,
                memory_span_used=0,
            ),
            completed=True,
            stage_name=stage_name,
        )