# tests/runtime/test_cognitive_scheduler.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.runtime.cognitive_process import (
    BudgetConsumption,
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


def test_scheduler_budget_exhausted_without_completion_sets_no_result():

    @dataclass
    class DummyOutcome:
        completed: bool
        result: object | None
        consumption: BudgetConsumption
        stage_name: str | None = "dummy_stage"

    def make_consumption() -> BudgetConsumption:
        return BudgetConsumption(
            reasoning_steps=1,
            attention_tokens=1,
            uncertainty_spent=0.0,
            elapsed_ms=1,
            memory_span_used=0,
        )

    class StubPipelineExecutor:
        def execute_process(self, process):
            return DummyOutcome(
                completed=False,
                result=None,
                consumption=make_consumption(),
                stage_name="dummy_stage",
            )

    runtime_state = CognitiveRuntimeState()
    executor = StubPipelineExecutor()
    scheduler = CognitiveScheduler(runtime_state, executor)  # type: ignore[arg-type]

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

    updated = runtime_state.get_process(CognitiveProcessId("p1"))

    assert decision.result is None
    assert updated.status == CognitiveProcessStatus.SUSPENDED
    assert runtime_state.scheduler_state.active_process_id is None
    assert CognitiveProcessId("p1") in runtime_state.scheduler_state.suspended_queue



def test_scheduler_preempts_incomplete_process_when_budget_remains():

    @dataclass
    class DummyOutcome:
        completed: bool
        result: object | None
        consumption: BudgetConsumption
        stage_name: str | None = "dummy_stage"

    def make_consumption() -> BudgetConsumption:
        return BudgetConsumption(
            reasoning_steps=1,
            attention_tokens=1,
            uncertainty_spent=0.0,
            elapsed_ms=1,
            memory_span_used=0,
        )

    class StubPipelineExecutor:
        def execute_process(self, process):
            return DummyOutcome(
                completed=False,
                result=None,
                consumption=make_consumption(),
                stage_name="dummy_stage",
            )

    runtime_state = CognitiveRuntimeState()
    executor = StubPipelineExecutor()
    scheduler = CognitiveScheduler(runtime_state, executor)  # type: ignore[arg-type]

    process = CognitiveProcess(
        process_id=CognitiveProcessId("p-preempt"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=2, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )

    scheduler.enqueue(process)
    decision = scheduler.tick()

    updated = runtime_state.get_process(CognitiveProcessId("p-preempt"))

    assert decision.result is None
    assert updated.status == CognitiveProcessStatus.READY
    assert runtime_state.scheduler_state.active_process_id is None
    assert CognitiveProcessId("p-preempt") in runtime_state.scheduler_state.ready_queue



def test_executor_raises_if_finalize_returns_none():
    class BadPipeline:
        def iter_stages(self):
            return []

        def _prepare_run(self, ctx): pass
        def finalize_run(self, ctx): return None

    executor = PipelineExecutor(BadPipeline())

    process = CognitiveProcess(
        process_id=CognitiveProcessId("bad"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10),
        budget=CognitiveBudget(reasoning_steps=1),
        local_state=CognitivePipelineContext(user_id="u", cognitive_input={}),
        created_tick=0,
        user_id="u",
    )

    import pytest
    with pytest.raises(RuntimeError):
        executor.execute_process(process)