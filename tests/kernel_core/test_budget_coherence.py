# tests/kernel_core/test_budget_coherence.py
"""has_budget and consume enforce the same dimensions.

Campaign HARDEN (DM-H2, audit P1-15c, 2026-09-02). has_budget checked
reasoning_steps alone while consume raised SchedulerInvariantViolation
on four dimensions (steps, attention, uncertainty, memory_span): a
process with zero attention tokens was schedulable, then exploded on
its first consumption. The two must speak the same contract; the
wall-clock dimension (time_slice_ms) stays audit-only on both sides,
per the documented rationale (non-deterministic, machine dependent).
"""

from __future__ import annotations

import pytest

from arvis.errors.runtime_scheduler import SchedulerInvariantViolation
from arvis.kernel_core.process.budget import BudgetConsumption, CognitiveBudget
from arvis.kernel_core.process.priority import CognitivePriority
from arvis.kernel_core.process.process_factory import ProcessFactory
from arvis.kernel_core.process.types import (
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)


def _process(budget: CognitiveBudget):
    return ProcessFactory.create(
        process_id=CognitiveProcessId("p1"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(50.0),
        budget=budget,
        created_tick=0,
        user_id="u1",
    )


@pytest.mark.parametrize(
    ("budget", "label"),
    [
        (CognitiveBudget(attention_tokens=0), "attention_tokens"),
        (CognitiveBudget(uncertainty_budget=0.0), "uncertainty_budget"),
        (CognitiveBudget(memory_span=0), "memory_span"),
        (CognitiveBudget(reasoning_steps=0), "reasoning_steps"),
    ],
    ids=["attention", "uncertainty", "memory_span", "reasoning_steps"],
)
def test_an_exhausted_enforced_dimension_means_no_budget(budget, label) -> None:
    process = _process(budget)
    assert process.has_budget() is False, (
        f"a process with zero {label} is reported schedulable, but "
        "consume() raises on that dimension (DM-H2): has_budget and "
        "consume must enforce the same contract"
    )


def test_exhausted_wall_clock_stays_schedulable() -> None:
    """time_slice_ms is audit-only on both sides: consume never raises
    on it and has_budget never gates on it (documented rationale)."""
    process = _process(CognitiveBudget(time_slice_ms=0))
    assert process.has_budget() is True
    process.consume(BudgetConsumption(elapsed_ms=10_000))
    assert process.has_budget() is True


def test_consume_still_raises_on_the_enforced_dimensions() -> None:
    process = _process(CognitiveBudget(attention_tokens=1))
    with pytest.raises(SchedulerInvariantViolation):
        process.consume(BudgetConsumption(attention_tokens=2))
