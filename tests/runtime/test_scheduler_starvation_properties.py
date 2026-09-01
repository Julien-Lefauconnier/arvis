# tests/runtime/test_scheduler_starvation_properties.py
"""Multi-tick scheduler properties: what actually prevents starvation.

Campaign STRUCT, LOT S5. The scheduling score is
``priority + age * age_bonus_per_tick - penalties`` with age counted
from ``created_tick``: every waiting process ages at the same rate, so
aging never closes a priority gap; it only orders processes of equal
priority by arrival. The mechanism that actually prevents starvation
is BUDGET DEPLETION: a running process consumes reasoning steps and
leaves the schedulable set when they run out. These properties pin
that mechanism over whole multi-tick runs, not single decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

from hypothesis import given, settings
from hypothesis import strategies as st

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel_core.process import (
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
class _Outcome:
    completed: bool
    result: object | None
    consumption: BudgetConsumption
    stage_name: str | None = "dummy"


class _CountingExecutor:
    """Never completes; consumes one reasoning step per slice."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute_process(self, process: CognitiveProcess) -> _Outcome:
        self.calls.append(process.process_id.value)
        return _Outcome(
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


def _process(
    pid: str, priority: float, steps: int, created_tick: int = 0
) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(pid),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(priority),
        budget=CognitiveBudget(reasoning_steps=steps, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id=pid, cognitive_input={}),
        created_tick=created_tick,
        user_id=pid,
    )


def _drive(
    scheduler: CognitiveScheduler, max_ticks: int, executor: _CountingExecutor
) -> None:
    for _ in range(max_ticks):
        decision = scheduler.tick()
        if decision.selected_process_id is None:
            break


@settings(max_examples=30, deadline=None)
@given(
    priorities=st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        min_size=2,
        max_size=6,
    ),
    steps=st.integers(min_value=1, max_value=4),
)
def test_every_budgeted_process_eventually_executes(
    priorities: list[float], steps: int
) -> None:
    """Starvation-freedom through budget depletion: with finite
    budgets, every process runs at least once within the total budget
    horizon, whatever the adversarial priority spread."""
    runtime_state = CognitiveRuntimeState()
    executor = _CountingExecutor()
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=executor
    )

    pids = []
    for i, prio in enumerate(priorities):
        pid = f"p{i}"
        pids.append(pid)
        scheduler.enqueue(_process(pid, priority=prio, steps=steps))

    horizon = steps * len(priorities) + len(priorities)
    _drive(scheduler, horizon, executor)

    executed = set(executor.calls)
    missing = set(pids) - executed
    assert not missing, (
        f"processes never scheduled within the budget horizon "
        f"({horizon} ticks): {sorted(missing)}; calls={executor.calls}"
    )


@settings(max_examples=30, deadline=None)
@given(
    priorities=st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        min_size=2,
        max_size=6,
    ),
)
def test_budget_bounds_any_single_process_run_share(
    priorities: list[float],
) -> None:
    """No process is executed more often than its budget allows: the
    depletion mechanism is what bounds the winner's share."""
    steps = 3
    runtime_state = CognitiveRuntimeState()
    executor = _CountingExecutor()
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=executor
    )

    for i, prio in enumerate(priorities):
        scheduler.enqueue(_process(f"p{i}", priority=prio, steps=steps))

    _drive(scheduler, steps * len(priorities) + len(priorities), executor)

    for i in range(len(priorities)):
        assert executor.calls.count(f"p{i}") <= steps, (
            f"p{i} executed more slices than its reasoning budget "
            f"({executor.calls.count(f'p{i}')} > {steps})"
        )


def test_equal_priority_first_executions_follow_arrival_order() -> None:
    """Aging orders equals by arrival: the first execution of each
    equal-priority process follows creation order across a whole run."""
    runtime_state = CognitiveRuntimeState()
    executor = _CountingExecutor()
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=executor
    )

    n = 4
    for i in range(n):
        scheduler.enqueue(_process(f"p{i}", priority=10.0, steps=2, created_tick=i))

    runtime_state.scheduler_state.tick_count = n

    _drive(scheduler, 3 * n, executor)

    firsts = {}
    for idx, pid in enumerate(executor.calls):
        firsts.setdefault(pid, idx)
    order = sorted(firsts, key=firsts.__getitem__)
    assert order == [f"p{i}" for i in range(n)], (
        f"first-execution order {order} does not follow arrival order"
    )


def test_priority_dominates_while_budget_lasts() -> None:
    """Honest limitation, pinned: aging cannot close a priority gap
    (all waiters age at the same rate), so a high-priority process
    runs UNINTERRUPTED until its budget depletes; only then does the
    lower-priority process run."""
    runtime_state = CognitiveRuntimeState()
    executor = _CountingExecutor()
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=executor
    )

    steps = 4
    scheduler.enqueue(_process("low", priority=5.0, steps=steps))
    scheduler.enqueue(_process("high", priority=90.0, steps=steps))

    _drive(scheduler, 2 * steps + 2, executor)

    assert executor.calls[:steps] == ["high"] * steps, (
        "the high-priority process must hold the scheduler until its "
        f"budget depletes (got {executor.calls[:steps]})"
    )
    assert "low" in executor.calls, (
        "budget depletion must eventually hand the scheduler to the "
        "low-priority process"
    )
