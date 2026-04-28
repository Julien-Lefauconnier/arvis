# tests/runtime/test_preemption_budget.py

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


@dataclass
class DummyOutcome:
    completed: bool
    result: object | None
    consumption: BudgetConsumption
    stage_name: str | None = "dummy_stage"


class IncompleteExecutor:
    def __init__(self, *, reasoning_steps=1, elapsed_ms=1):
        self.reasoning_steps = reasoning_steps
        self.elapsed_ms = elapsed_ms
        self.calls = 0

    def execute_process(self, process):
        self.calls += 1
        return DummyOutcome(
            completed=False,
            result=None,
            consumption=BudgetConsumption(
                reasoning_steps=self.reasoning_steps,
                attention_tokens=0,
                uncertainty_spent=0.0,
                elapsed_ms=self.elapsed_ms,
                memory_span_used=0,
            ),
            stage_name="step",
        )


def make_process(process_id: str, *, budget_steps: int) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(process_id),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=budget_steps, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )


def test_unfinished_with_remaining_budget_is_requeued():
    runtime_state = CognitiveRuntimeState()
    executor = IncompleteExecutor(reasoning_steps=1)
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=executor
    )

    process = make_process("p1", budget_steps=2)
    scheduler.enqueue(process)

    decision = scheduler.tick()
    updated = runtime_state.get_process(process.process_id)

    assert decision.result is None
    assert updated.status == CognitiveProcessStatus.READY
    assert process.process_id in runtime_state.scheduler_state.ready_queue
    assert executor.calls == 1


def test_unfinished_without_remaining_budget_is_suspended():
    runtime_state = CognitiveRuntimeState()
    executor = IncompleteExecutor(reasoning_steps=1)
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=executor
    )

    process = make_process("p2", budget_steps=1)
    scheduler.enqueue(process)

    decision = scheduler.tick()
    updated = runtime_state.get_process(process.process_id)

    assert decision.result is None
    assert updated.status == CognitiveProcessStatus.SUSPENDED
    assert process.process_id in runtime_state.scheduler_state.suspended_queue
    assert executor.calls == 1


def test_single_tick_executes_single_step():
    runtime_state = CognitiveRuntimeState()
    executor = IncompleteExecutor(reasoning_steps=1)
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=executor
    )

    process = make_process("p3", budget_steps=3)
    scheduler.enqueue(process)

    scheduler.tick()
    assert executor.calls == 1

    scheduler.tick()
    assert executor.calls == 2
