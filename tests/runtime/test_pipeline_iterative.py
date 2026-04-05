# tests/runtime/test_pipeline_iterative.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.runtime.pipeline_executor import PipelineExecutor

from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.cognitive_scheduler import CognitiveScheduler
from arvis.runtime.cognitive_process import (
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
    CognitivePriority,
    CognitiveBudget,
)
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext

class DummyPipeline:
    def run(self, ctx):
        class Result:
            can_execute = True
            requires_confirmation = False
        return Result()

def test_iter_stages_order_matches_pipeline():


    pipeline = CognitivePipeline()

    stages = list(pipeline.iter_stages())

    assert len(stages) > 0
    assert stages[0].__class__.__name__ == "ToolFeedbackStage"
    assert stages[-1].__class__.__name__ == "RuntimeStage"


def test_run_iter_executes_all_stages_without_error():


    pipeline = CognitivePipeline()
    ctx = CognitivePipelineContext(user_id="u1", cognitive_input={})

    executed = []

    for stage in pipeline.run_iter(ctx):
        executed.append(stage.__class__.__name__)

    assert len(executed) > 0


def test_iterative_and_classic_pipeline_do_not_crash():

    pipeline = CognitivePipeline()

    ctx1 = CognitivePipelineContext(user_id="u1", cognitive_input={})
    ctx2 = CognitivePipelineContext(user_id="u1", cognitive_input={})

    result_classic = pipeline.run(ctx1)

    for _ in pipeline.run_iter(ctx2):
        pass

    # pas d’assert strict → juste vérifier stabilité
    assert result_classic is not None


def test_scheduler_with_iterative_executor():

    runtime_state = CognitiveRuntimeState()
    executor = PipelineExecutor(pipeline=DummyPipeline())
    executor.use_iterative = True

    scheduler = CognitiveScheduler(runtime_state=runtime_state, pipeline_executor=executor)

    process = CognitiveProcess(
        process_id=CognitiveProcessId("p1"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=1, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )

    scheduler.enqueue(process)
    decision = scheduler.tick()

    assert decision.selected_process_id is not None