# tests/errors/test_error_policy.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisDegradedModeError,
    ArvisExternalError,
    ArvisRuntimeError,
)
from arvis.errors.policy import decide_error_policy


def test_runtime_error_policy_decision():
    decision = decide_error_policy(ArvisRuntimeError("runtime"))

    assert decision.halt_process is True
    assert decision.retry is False


def test_external_error_policy_decision():
    decision = decide_error_policy(ArvisExternalError("external"))

    assert decision.retry is True
    assert decision.halt_process is False


def test_degraded_error_policy_decision():
    decision = decide_error_policy(ArvisDegradedModeError("degraded"))

    assert decision.degrade is True


def test_policy_decision_observable():
    decision = decide_error_policy(ArvisRuntimeError("runtime"))

    assert decision.observable is True


def test_policy_decision_recoverable():
    decision = decide_error_policy(ArvisDegradedModeError("degraded"))

    assert decision.recoverable is True
