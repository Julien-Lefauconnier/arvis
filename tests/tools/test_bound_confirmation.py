# tests/tools/test_bound_confirmation.py
"""Bound tool confirmations (P1-10-a6, decision D4-d: full object).

A spec-declared confirmation requirement is satisfiable, and only by a
registry record bound to the exact effect: tool name, canonical hash of
the redacted payload, principal, tenant. Single use, optional expiry.
A mismatched attempt never consumes a legitimate confirmation; a
consumed one cannot be replayed; without a registry or a valid id the
requirement stays refused.
"""

import time
from types import SimpleNamespace

from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry, payload_commitment
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _SensitiveTool(BaseTool):
    name = "sensitive_tool"
    spec = ToolSpec(
        name="sensitive_tool",
        description="probe",
        requires_confirmation=True,
    )

    def __init__(self) -> None:
        self.executed: list = []

    def execute_invocation(self, invocation):
        self.executed.append(invocation)
        return {"ok": True}

    def execute(self, input_data):  # pragma: no cover
        raise AssertionError("legacy path must not be used")


# ---------------------------------------------------------------
# Registry semantics
# ---------------------------------------------------------------


def test_issue_and_consume_on_exact_match():
    registry = ConfirmationRegistry()
    record = registry.issue(
        tool_name="t", payload={"a": 1}, principal="u1", tenant="org"
    )
    consumed = registry.consume(
        confirmation_id=record.confirmation_id,
        tool_name="t",
        payload={"a": 1},
        principal="u1",
        tenant="org",
    )
    assert consumed is not None
    assert consumed.payload_sha256 == payload_commitment({"a": 1})


def test_confirmation_is_single_use():
    registry = ConfirmationRegistry()
    record = registry.issue(tool_name="t", payload={"a": 1}, principal="u1")
    assert (
        registry.consume(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"a": 1},
            principal="u1",
        )
        is not None
    )
    assert (
        registry.consume(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"a": 1},
            principal="u1",
        )
        is None
    )


def test_confirmation_is_bound_to_payload_and_principal():
    registry = ConfirmationRegistry()
    record = registry.issue(tool_name="t", payload={"a": 1}, principal="u1")

    # Any binding mismatch refuses AND does not burn the record.
    for kwargs in (
        {"tool_name": "other", "payload": {"a": 1}, "principal": "u1"},
        {"tool_name": "t", "payload": {"a": 2}, "principal": "u1"},
        {"tool_name": "t", "payload": {"a": 1}, "principal": "u2"},
        {"tool_name": "t", "payload": {"a": 1}, "principal": "u1", "tenant": "x"},
    ):
        assert (
            registry.consume(confirmation_id=record.confirmation_id, **kwargs) is None
        )
        assert registry.pending_count() == 1

    # The exact match still consumes afterwards.
    assert (
        registry.consume(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"a": 1},
            principal="u1",
        )
        is not None
    )


def test_expired_confirmation_is_refused_and_purged():
    registry = ConfirmationRegistry()
    record = registry.issue(tool_name="t", payload={}, principal="u1", ttl_seconds=0.01)
    time.sleep(0.03)
    assert (
        registry.consume(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={},
            principal="u1",
        )
        is None
    )
    assert registry.pending_count() == 0


# ---------------------------------------------------------------
# Manager and policy, end to end
# ---------------------------------------------------------------


def _manager_with(registry_of_confirmations):
    tools = ToolRegistry()
    tool = _SensitiveTool()
    tools.register(tool)
    manager = ToolManager(
        tools,
        ToolExecutor(tools),
        confirmation_registry=registry_of_confirmations,
    )
    return manager, tool


def _turn(manager, ctx):
    decision = SimpleNamespace(tool="sensitive_tool", tool_payload={"cmd": "go"})
    result = SimpleNamespace(action_decision=decision)
    return manager.run(result, ctx)


def test_confirmed_invocation_satisfies_the_requirement():
    confirmations = ConfirmationRegistry()
    record = confirmations.issue(
        tool_name="sensitive_tool", payload={"cmd": "go"}, principal="u1"
    )
    manager, tool = _manager_with(confirmations)
    ctx = SimpleNamespace(
        extra={},
        user_id="u1",
        confirmation_result=SimpleNamespace(
            confirmed=True, confirmation_id=record.confirmation_id
        ),
    )
    outcome = _turn(manager, ctx)
    assert outcome is not None and outcome.success is True
    invocation = tool.executed[0]
    assert invocation.confirmed is True
    assert invocation.confirmation_id == record.confirmation_id
    assert invocation.confirmation_commitment == payload_commitment({"cmd": "go"})


def test_unconfirmed_invocation_stays_refused():
    manager, tool = _manager_with(ConfirmationRegistry())
    ctx = SimpleNamespace(extra={}, user_id="u1")
    outcome = _turn(manager, ctx)
    assert outcome is not None and outcome.success is False
    assert "confirmation_required" in str(outcome.error)
    assert tool.executed == []


def test_wrong_confirmation_id_stays_refused():
    confirmations = ConfirmationRegistry()
    confirmations.issue(
        tool_name="sensitive_tool", payload={"cmd": "go"}, principal="u1"
    )
    manager, tool = _manager_with(confirmations)
    ctx = SimpleNamespace(
        extra={},
        user_id="u1",
        confirmation_result=SimpleNamespace(confirmed=True, confirmation_id="forged"),
    )
    outcome = _turn(manager, ctx)
    assert outcome is not None and outcome.success is False
    assert tool.executed == []
    # The legitimate record was not burnt by the forged attempt.
    assert confirmations.pending_count() == 1


def test_consumed_confirmation_cannot_authorize_a_second_turn():
    confirmations = ConfirmationRegistry()
    record = confirmations.issue(
        tool_name="sensitive_tool", payload={"cmd": "go"}, principal="u1"
    )
    manager, tool = _manager_with(confirmations)
    carrier = SimpleNamespace(confirmed=True, confirmation_id=record.confirmation_id)
    ctx = SimpleNamespace(extra={}, user_id="u1", confirmation_result=carrier)
    first = _turn(manager, ctx)
    assert first is not None and first.success is True
    second = _turn(manager, ctx)
    assert second is not None and second.success is False
    assert len(tool.executed) == 1
