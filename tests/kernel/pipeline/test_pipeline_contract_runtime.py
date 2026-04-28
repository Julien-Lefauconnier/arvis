# tests/runtime/test_pipeline_contract_runtime.py

from __future__ import annotations

import pytest

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.pipeline.pipeline_contract import (
    PipelineFinalizeSignal,
    PipelineStageSignal,
)
from arvis.runtime.cognitive_process import (
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)
from arvis.runtime.pipeline_executor import PipelineExecutor


def make_process(process_id: str = "p1", reasoning_steps: int = 3) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(process_id),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=reasoning_steps, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )


def test_executor_accepts_explicit_stage_signal():
    class TwoStagePipeline:
        def iter_stages(self):
            return [object(), object()]

        def _prepare_run(self, ctx):
            pass

        def run_stage(self, ctx, stage):
            return PipelineStageSignal(completed=False, result=None)

        def finalize_run(self, ctx):
            return PipelineFinalizeSignal(result={"done": True})

    executor = PipelineExecutor(TwoStagePipeline())  # type: ignore[arg-type]
    process = make_process()

    outcome1 = executor.execute_process(process)
    assert outcome1.completed is False
    assert outcome1.result is None
    assert outcome1.stage_name is not None


def test_executor_accepts_explicit_finalize_signal():
    class NoStagePipeline:
        def iter_stages(self):
            return []

        def _prepare_run(self, ctx):
            pass

        def finalize_run(self, ctx):
            return PipelineFinalizeSignal(result={"ok": True})

    executor = PipelineExecutor(NoStagePipeline())  # type: ignore[arg-type]
    process = make_process()

    outcome = executor.execute_process(process)
    assert outcome.completed is True
    assert outcome.result == {"ok": True}
    assert outcome.stage_name == "FinalizeRun"


def test_executor_rejects_none_finalize_result():
    class BadPipeline:
        def iter_stages(self):
            return []

        def _prepare_run(self, ctx):
            pass

        def finalize_run(self, ctx):
            return None

    executor = PipelineExecutor(BadPipeline())  # type: ignore[arg-type]
    process = make_process()

    with pytest.raises(RuntimeError, match="finalize_run returned None"):
        executor.execute_process(process)


def test_executor_rejects_stage_level_finalization():
    class BadStagePipeline:
        def iter_stages(self):
            return [object()]

        def _prepare_run(self, ctx):
            pass

        def run_stage(self, ctx, stage):
            return PipelineStageSignal(completed=True, result={"bad": True})

        def finalize_run(self, ctx):
            return PipelineFinalizeSignal(result={"ok": True})

    executor = PipelineExecutor(BadStagePipeline())  # type: ignore[arg-type]
    process = make_process()

    with pytest.raises(RuntimeError, match="must not finalize the pipeline directly"):
        executor.execute_process(process)


def test_executor_keeps_backward_compat_for_legacy_stage_returning_none():
    class LegacyPipeline:
        def iter_stages(self):
            return [object()]

        def _prepare_run(self, ctx):
            pass

        def run_stage(self, ctx, stage):
            return None  # legacy behavior

        def finalize_run(self, ctx):
            return {"done": True}

    executor = PipelineExecutor(LegacyPipeline())  # type: ignore[arg-type]
    process = make_process()

    outcome = executor.execute_process(process)
    assert outcome.completed is False
    assert outcome.result is None
