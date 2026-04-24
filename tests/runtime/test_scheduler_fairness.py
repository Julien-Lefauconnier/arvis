# tests/runtime/test_scheduler_fairness.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.cognitive_scheduler import CognitiveScheduler
from arvis.kernel_core.process import (
    BudgetConsumption,
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)


@dataclass
class DummyOutcome:
    completed: bool
    result: object | None
    consumption: BudgetConsumption
    stage_name: str | None = "dummy"


class NonCompletingExecutor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute_process(self, process):
        self.calls.append(process.process_id.value)
        return DummyOutcome(
            completed=False,
            result=None,
            consumption=BudgetConsumption(
                reasoning_steps=1,
                attention_tokens=0,
                uncertainty_spent=0.0,
                elapsed_ms=1,
                memory_span_used=0,
            ),
        )


def make_process(pid: str, priority: float, created_tick: int = 0) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(pid),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(priority),
        budget=CognitiveBudget(reasoning_steps=3, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id=pid, cognitive_input={}),
        created_tick=created_tick,
        user_id=pid,
    )


def test_higher_priority_process_selected_first():
    runtime_state = CognitiveRuntimeState()
    executor = NonCompletingExecutor()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=executor)

    low = make_process("low", priority=10.0)
    high = make_process("high", priority=50.0)

    scheduler.enqueue(low)
    scheduler.enqueue(high)

    decision = scheduler.tick()

    assert decision.selected_process_id is not None
    assert decision.selected_process_id.value == "high"
    assert executor.calls == ["high"]


def test_age_bonus_can_break_tie_over_time():
    runtime_state = CognitiveRuntimeState()
    executor = NonCompletingExecutor()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=executor)

    older = make_process("older", priority=10.0, created_tick=0)
    newer = make_process("newer", priority=10.0, created_tick=5)

    runtime_state.scheduler_state.tick_count = 10

    scheduler.enqueue(older)
    scheduler.enqueue(newer)

    decision = scheduler.tick()

    assert decision.selected_process_id is not None
    assert decision.selected_process_id.value == "older"


def test_non_schedulable_process_is_skipped():
    runtime_state = CognitiveRuntimeState()
    executor = NonCompletingExecutor()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=executor)

    exhausted = CognitiveProcess(
        process_id=CognitiveProcessId("exhausted"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(100.0),
        budget=CognitiveBudget(reasoning_steps=0, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u", cognitive_input={}),
        created_tick=0,
        user_id="u",
    )

    normal = make_process("normal", priority=10.0)

    scheduler.enqueue(normal)
    runtime_state.processes[exhausted.process_id] = exhausted
    runtime_state.scheduler_state.append_unique(
        runtime_state.scheduler_state.ready_queue,
        exhausted.process_id,
    )

    decision = scheduler.tick()

    assert decision.selected_process_id is not None
    assert decision.selected_process_id.value == "normal"
    assert executor.calls == ["normal"]