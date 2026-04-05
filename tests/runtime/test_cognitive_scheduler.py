# tests/runtime/test_cognitive_scheduler.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.runtime.cognitive_process import (
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.cognitive_scheduler import CognitiveScheduler
from arvis.runtime.pipeline_executor import PipelineExecutor


@dataclass
class DummyPipelineResult:
    can_execute: bool = True
    requires_confirmation: bool = False


class DummyPipeline:
    def run(self, ctx):
        return DummyPipelineResult()


def test_scheduler_executes_highest_priority_process():
    runtime_state = CognitiveRuntimeState()
    executor = PipelineExecutor(pipeline=DummyPipeline())  # type: ignore[arg-type]
    scheduler = CognitiveScheduler(runtime_state=runtime_state, pipeline_executor=executor)

    p1 = CognitiveProcess(
        process_id=CognitiveProcessId("p1"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=1, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )

    p2 = CognitiveProcess(
        process_id=CognitiveProcessId("p2"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(50.0),
        budget=CognitiveBudget(reasoning_steps=1, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u2", cognitive_input={}),
        created_tick=0,
        user_id="u2",
    )

    scheduler.enqueue(p1)
    scheduler.enqueue(p2)

    decision = scheduler.tick()

    assert decision.selected_process_id is not None
    assert decision.selected_process_id.value == "p2"

    process = runtime_state.get_process(CognitiveProcessId("p2"))
    # In iterative scheduler, a single tick may not complete the process
    assert process.status in [
        CognitiveProcessStatus.READY,
        CognitiveProcessStatus.COMPLETED,
        CognitiveProcessStatus.WAITING_CONFIRMATION,
    ]


def test_scheduler_waits_confirmation_when_pipeline_requires_it():
    class ConfirmationPipeline:
        def run(self, ctx):
            return DummyPipelineResult(can_execute=False, requires_confirmation=True)

    runtime_state = CognitiveRuntimeState()
    executor = PipelineExecutor(pipeline=ConfirmationPipeline())  # type: ignore[arg-type]
    scheduler = CognitiveScheduler(runtime_state=runtime_state, pipeline_executor=executor)

    process = CognitiveProcess(
        process_id=CognitiveProcessId("p-confirm"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(30.0),
        budget=CognitiveBudget(reasoning_steps=1, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )

    scheduler.enqueue(process)
    # Run until process reaches terminal state
    for _ in range(10):
        scheduler.tick()
        updated = runtime_state.get_process(CognitiveProcessId("p-confirm"))

        if updated.status in [
            CognitiveProcessStatus.WAITING_CONFIRMATION,
            CognitiveProcessStatus.COMPLETED,
        ]:
            break

    updated = runtime_state.get_process(CognitiveProcessId("p-confirm"))
    assert updated.status == CognitiveProcessStatus.WAITING_CONFIRMATION