# arvis/runtime/pipeline_executor.py

from __future__ import annotations

from time import perf_counter
from typing import Any, Optional, cast

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.pipeline.pipeline_contract import (
    PipelineFinalizeSignal,
    PipelineStageSignal,
)
from arvis.kernel_core.process import BudgetConsumption, CognitiveProcess
from arvis.kernel_core.contracts.execution_contract import ProcessExecutionOutcome


class PipelineExecutor:
    """
    Concrete execution adapter that runs CognitivePipeline behind
    the kernel-level ProcessExecutor contract.
    """

    def __init__(self, pipeline: CognitivePipeline):
        self.pipeline = pipeline
        self.use_iterative = True

    def execute_process(self, process: CognitiveProcess) -> ProcessExecutionOutcome:
        ctx = process.local_state
        if not isinstance(ctx, CognitivePipelineContext):
            raise TypeError("process.local_state must be a CognitivePipelineContext")

        start = perf_counter()

        if not hasattr(self.pipeline, "iter_stages"):
            return self._run_full_pipeline(ctx, start, "DirectRun")

        if not self.use_iterative:
            return self._run_full_pipeline(ctx, start, "NonIterativeRun")

        stages = list(self.pipeline.iter_stages())
        if process.total_stage_count is None:
            process.set_total_stage_count(len(stages))

        if not process.pipeline_prepared:
            self.pipeline._prepare_run(ctx)
            process.mark_pipeline_prepared()

        if process.has_remaining_stages():
            stage = stages[process.current_stage_index]
            stage_result = cast(
                Optional[PipelineStageSignal],
                self.pipeline.run_stage(ctx, stage),
            )
            process.advance_stage(stage.__class__.__name__)

            if isinstance(stage_result, PipelineStageSignal):
                completed = stage_result.completed
                result = stage_result.result
            else:
                completed = False
                result = None

            if completed:
                raise RuntimeError(
                    "run_stage() must not finalize the pipeline directly; "
                    "use finalize_run() for terminal completion"
                )

            stage_name = stage.__class__.__name__

        else:
            finalize_result = self.pipeline.finalize_run(ctx)
            result = self._normalize_finalize_result(finalize_result)
            process.mark_pipeline_finalized()
            completed = True
            stage_name = "FinalizeRun"

        elapsed_ms = max(1, int((perf_counter() - start) * 1000.0))

        return ProcessExecutionOutcome(
            result=result,
            consumption=BudgetConsumption(
                reasoning_steps=1,
                attention_tokens=1,
                uncertainty_spent=0.0,
                elapsed_ms=elapsed_ms,
                memory_span_used=0,
            ),
            completed=completed,
            stage_name=stage_name,
        )

    def _normalize_finalize_result(self, finalize_result: Any) -> Any:
        if isinstance(finalize_result, PipelineFinalizeSignal):
            if not finalize_result.completed:
                raise RuntimeError(
                    "PipelineFinalizeSignal.completed must be True in finalize_run()"
                )
            if finalize_result.result is None:
                raise RuntimeError(
                    "PipelineFinalizeSignal.result must not be None in finalize_run()"
                )
            return finalize_result.result

        if finalize_result is None:
            raise RuntimeError("Pipeline finalize_run returned None")

        return finalize_result

    def _run_full_pipeline(
        self,
        ctx: CognitivePipelineContext,
        start: float,
        stage_name: str,
    ) -> ProcessExecutionOutcome:
        result = self.pipeline.run(ctx)
        if result is None:
            raise RuntimeError("Pipeline run(ctx) returned None")

        elapsed_ms = max(1, int((perf_counter() - start) * 1000.0))

        return ProcessExecutionOutcome(
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