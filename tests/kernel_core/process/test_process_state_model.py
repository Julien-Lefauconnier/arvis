# tests/kernel_core/process/test_process_state_model.py

from __future__ import annotations

import pytest

from arvis.kernel_core.process import (
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
    BudgetConsumption,
)
from arvis.kernel_core.process.transitions import InvalidTransitionError


def make_process(status=CognitiveProcessStatus.READY):
    return CognitiveProcess(
        process_id=CognitiveProcessId("p1"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=status,
        priority=CognitivePriority(50.0),
        budget=CognitiveBudget(
            reasoning_steps=5,
            attention_tokens=100,
            uncertainty_budget=1.0,
            time_slice_ms=50,
            memory_span=10,
        ),
        created_tick=0,
        user_id="u1",
    )


def test_v1_constructor_works():
    proc = make_process()
    assert proc.process_id.value == "p1"
    assert proc.status == CognitiveProcessStatus.READY


def test_is_final_states():
    assert make_process(CognitiveProcessStatus.COMPLETED).is_final() is True
    assert make_process(CognitiveProcessStatus.ABORTED).is_final() is True
    assert make_process(CognitiveProcessStatus.READY).is_final() is False


def test_is_schedulable():
    proc = make_process()
    assert proc.is_schedulable() is True

    proc.mark_running(tick=1, score=10.0)
    proc.mark_blocked("io")

    assert proc.is_schedulable() is False


def test_remaining_budget_after_consume():
    proc = make_process()

    proc.consume(
        BudgetConsumption(
            reasoning_steps=2,
            elapsed_ms=10,
        )
    )

    rem = proc.remaining_budget()

    assert rem.reasoning_steps == 3
    assert rem.time_slice_ms == 40


def test_mark_completed_sets_terminal():
    proc = make_process()

    proc.mark_running(tick=1, score=10.0)
    proc.mark_completed(result={"ok": True})

    assert proc.status == CognitiveProcessStatus.COMPLETED
    assert proc.last_result == {"ok": True}


def test_invalid_transition_ready_to_completed_direct():
    proc = make_process()

    with pytest.raises(InvalidTransitionError):
        proc.mark_completed(result={"ok": True})


def test_validate_rejects_empty_process_id():
    proc = CognitiveProcess(
        process_id=CognitiveProcessId(""),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(50.0),
        budget=CognitiveBudget(
            reasoning_steps=5,
            attention_tokens=100,
            uncertainty_budget=1.0,
            time_slice_ms=50,
            memory_span=10,
        ),
        created_tick=0,
        user_id="u1",
    )

    with pytest.raises(ValueError, match="process_id.value must not be empty"):
        proc.validate()
