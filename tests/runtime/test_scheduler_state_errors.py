# tests/runtime/test_scheduler_state_errors.py

from __future__ import annotations

import pytest

from arvis.errors.runtime_scheduler import (
    SchedulerInvariantViolation,
)
from arvis.kernel_core.state.scheduler_state import SchedulerState


def test_single_running_invariant_violation():
    state = SchedulerState()

    with pytest.raises(
        SchedulerInvariantViolation,
        match="more than one RUNNING process",
    ) as exc_info:
        state.validate_single_running_invariant(2)

    error = exc_info.value

    assert error.code == "scheduler_invariant_violation"

    assert error.details["invariant"] == "single_running_process"

    assert error.details["running_count"] == 2

    assert error.details["retry_class"] == "permanent"

    assert error.replay_safe is False
