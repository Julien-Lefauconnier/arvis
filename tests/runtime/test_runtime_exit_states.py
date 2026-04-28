# tests/runtime/test_runtime_exit_states.py

from __future__ import annotations

from dataclasses import dataclass

import pytest

from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.kernel_core.process import CognitiveProcessStatus


@dataclass
class DummyResult:
    can_execute: bool = True
    requires_confirmation: bool = False
    action_decision: object | None = None


@dataclass
class DummyOutcome:
    completed: bool
    result: object | None
    consumption: object
    stage_name: str = "test"


class DummyConsumption:
    reasoning_steps = 0
    attention_tokens = 0
    uncertainty_spent = 0.0
    elapsed_ms = 0
    memory_span_used = 0

    def validate(self) -> None:
        return None


def make_os_with_executor(executor) -> CognitiveOS:
    os = CognitiveOS(config=CognitiveOSConfig(enable_trace=False))
    os.runtime.scheduler.process_executor = executor
    return os


class CompleteExecutor:
    def execute_process(self, process):
        return DummyOutcome(
            completed=True,
            result=DummyResult(),
            consumption=DummyConsumption(),
        )


class WaitingConfirmationExecutor:
    def execute_process(self, process):
        return DummyOutcome(
            completed=True,
            result=DummyResult(can_execute=False, requires_confirmation=True),
            consumption=DummyConsumption(),
        )


class BlockedExecutor:
    def execute_process(self, process):
        return DummyOutcome(
            completed=True,
            result=DummyResult(can_execute=False, requires_confirmation=False),
            consumption=DummyConsumption(),
        )


class AbortedExecutor:
    def execute_process(self, process):
        raise RuntimeError("boom")


class NoResultExecutor:
    def execute_process(self, process):
        return DummyOutcome(
            completed=False,
            result=None,
            consumption=DummyConsumption(),
        )


def test_runtime_returns_result_when_completed():
    os = make_os_with_executor(CompleteExecutor())

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None
    processes = list(os.runtime.runtime_state.processes.values())
    assert len(processes) == 1
    assert processes[0].status == CognitiveProcessStatus.COMPLETED


def test_runtime_returns_result_when_waiting_confirmation():
    os = make_os_with_executor(WaitingConfirmationExecutor())

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None
    processes = list(os.runtime.runtime_state.processes.values())
    assert len(processes) == 1
    assert processes[0].status == CognitiveProcessStatus.WAITING_CONFIRMATION


def test_runtime_returns_result_when_blocked():
    os = make_os_with_executor(BlockedExecutor())

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None
    processes = list(os.runtime.runtime_state.processes.values())
    assert len(processes) == 1
    assert processes[0].status == CognitiveProcessStatus.BLOCKED


def test_runtime_raises_when_aborted():
    os = make_os_with_executor(AbortedExecutor())

    with pytest.raises(RuntimeError, match="Process aborted"):
        os.run(user_id="u1", cognitive_input={})


def test_runtime_raises_when_no_result_is_produced():
    os = make_os_with_executor(NoResultExecutor())

    with pytest.raises(RuntimeError, match="Execution did not produce any result"):
        os.run(user_id="u1", cognitive_input={})
