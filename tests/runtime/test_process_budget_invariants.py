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
