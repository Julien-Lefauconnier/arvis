# arvis/runtime/pipeline_executor.py

from __future__ import annotations

from time import perf_counter

from arvis.errors.runtime_pipeline import (
    InvalidPipelineContextError,
    PipelineRuntimeError,
)
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel_core.contracts.execution_contract import ProcessExecutionOutcome
from arvis.kernel_core.process import BudgetConsumption, CognitiveProcess


class PipelineExecutor:
    """Runs CognitivePipeline behind the kernel ProcessExecutor contract.

    One stage per scheduler slice, then a finalize slice. The pipeline
    is typed and total here: ``run_stage`` returns None by contract and
    ``finalize_run`` returns the pipeline result (campaign STRUCT,
    LOT S2 removed the speculative signal-unwrapping machinery and the
    duck-typing guards that served pipelines this executor can no
    longer receive).
    """

    def __init__(self, pipeline: CognitivePipeline):
        self.pipeline = pipeline

    def execute_process(self, process: CognitiveProcess) -> ProcessExecutionOutcome:
        ctx = process.local_state
        if not isinstance(ctx, CognitivePipelineContext):
            raise InvalidPipelineContextError(
                "process.local_state must be a CognitivePipelineContext"
            )

        start = perf_counter()

        stages = list(self.pipeline.iter_stages())
        if process.total_stage_count is None:
            process.set_total_stage_count(len(stages))

        if not process.pipeline_prepared:
            self.pipeline._prepare_run(ctx)
            process.mark_pipeline_prepared()

        if process.has_remaining_stages():
            stage = stages[process.current_stage_index]
            self.pipeline.run_stage(ctx, stage)
            process.advance_stage(stage.__class__.__name__)

            completed = False
            result: object | None = None
            stage_name = stage.__class__.__name__
        else:
            result = self.pipeline.finalize_run(ctx)
            if result is None:
                # Fail-closed runtime guard on the typed contract: a
                # finalize that produced nothing must abort the run,
                # never hand the scheduler a silent None result.
                raise PipelineRuntimeError("Pipeline finalize_run returned None")
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
