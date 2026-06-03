# tests/runtime/test_process_budget_invariants.py

from __future__ import annotations

import pytest

from arvis.errors.runtime_scheduler import (
    SchedulerInvariantViolation,
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


def test_budget_underflow_detection():
    process = CognitiveProcess(
        process_id=CognitiveProcessId("p1"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(1.0),
        budget=CognitiveBudget(
            reasoning_steps=1,
            time_slice_ms=10,
        ),
        created_tick=0,
    )

    with pytest.raises(
        SchedulerInvariantViolation,
        match="Process budget underflow detected",
    ):
        process.consume(
            BudgetConsumption(
                reasoning_steps=999,
                elapsed_ms=1,
            )
        )


def test_time_slice_overrun_does_not_abort():
    """Wall-clock time is observability, not a governance invariant: exceeding
    time_slice_ms must NOT raise. Runaway stays bounded by reasoning_steps."""
    process = CognitiveProcess(
        process_id=CognitiveProcessId("p_time"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(1.0),
        budget=CognitiveBudget(reasoning_steps=40, time_slice_ms=100),
        created_tick=0,
    )

    # Exceeds the time slice (185 > 100) but stays within cognitive budgets.
    process.consume(BudgetConsumption(reasoning_steps=1, elapsed_ms=185))

    # No abort, and the time is still measured for audit.
    assert process.runtime.consumed_elapsed_ms == 185

    # Cognitive runaway is still enforced deterministically by steps.
    with pytest.raises(
        SchedulerInvariantViolation, match="Process budget underflow detected"
    ):
        process.consume(BudgetConsumption(reasoning_steps=999, elapsed_ms=0))
