# tests/tools/test_confirmation_transactional.py
"""Versioned, transactional confirmations (campaign 5, Lot 3).

Two guarantees on top of the injective binding of Lot 1:

- **D-3 versioning.** A record carries an explicit format version; a
  record of any other version is refused at reservation. The Lot 1 hash
  change means no a7-era confirmation is honoured.
- **D-4 reserve / commit / release (closes P1-5).** A confirmation is
  reserved (validated and locked, not removed) before the effect is
  authorized, committed once the effect runs, or released back to the
  pool if the effect is refused before running. A legitimate
  confirmation is never burned by a pre-effect denial, and never
  double-spent.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from arvis.tools.base import BaseTool
from arvis.tools.confirmation import (
    CONFIRMATION_FORMAT_VERSION,
    ConfirmationRegistry,
)
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec

# ---------------------------------------------------------------
# D-3: explicit format version
# ---------------------------------------------------------------


def test_issued_record_carries_current_format_version():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    assert record.format_version == CONFIRMATION_FORMAT_VERSION


def test_reserve_refuses_a_record_of_a_foreign_version():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    # Simulate an a7-era record smuggled into the store with an old
    # version: reservation must refuse it.
    stale = replace(record, format_version=1)
    reg._records[record.confirmation_id].confirmation = stale
    assert (
        reg.reserve(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"id": "A"},
            principal="u1",
        )
        is None
    )


# ---------------------------------------------------------------
# D-4: reserve / commit / release lifecycle
# ---------------------------------------------------------------


def test_reserve_locks_without_removing():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    reserved = reg.reserve(
        confirmation_id=record.confirmation_id,
        tool_name="t",
        payload={"id": "A"},
        principal="u1",
    )
    assert reserved is not None
    assert reg.pending_count() == 1  # still present, just locked


def test_reserved_record_cannot_be_reserved_again():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    reg.reserve(
        confirmation_id=record.confirmation_id,
        tool_name="t",
        payload={"id": "A"},
        principal="u1",
    )
    assert (
        reg.reserve(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"id": "A"},
            principal="u1",
        )
        is None
    )


def test_commit_removes_the_reserved_record():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    reg.reserve(
        confirmation_id=record.confirmation_id,
        tool_name="t",
        payload={"id": "A"},
        principal="u1",
    )
    assert reg.commit(confirmation_id=record.confirmation_id) is True
    assert reg.pending_count() == 0


def test_release_returns_the_record_to_the_pool():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    reg.reserve(
        confirmation_id=record.confirmation_id,
        tool_name="t",
        payload={"id": "A"},
        principal="u1",
    )
    assert reg.release(confirmation_id=record.confirmation_id) is True
    # Reservable again after release.
    assert (
        reg.reserve(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"id": "A"},
            principal="u1",
        )
        is not None
    )


def test_commit_without_reservation_is_a_noop():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    assert reg.commit(confirmation_id=record.confirmation_id) is False
    assert reg.pending_count() == 1


def test_mismatch_never_reserves():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    assert (
        reg.reserve(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"id": "B"},
            principal="u1",
        )
        is None
    )
    # The record survives, unreserved, for its real effect.
    assert (
        reg.reserve(
            confirmation_id=record.confirmation_id,
            tool_name="t",
            payload={"id": "A"},
            principal="u1",
        )
        is not None
    )


def test_consume_is_reserve_then_commit():
    reg = ConfirmationRegistry()
    record = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    consumed = reg.consume(
        confirmation_id=record.confirmation_id,
        tool_name="t",
        payload={"id": "A"},
        principal="u1",
    )
    assert consumed is not None
    assert reg.pending_count() == 0


# ---------------------------------------------------------------
# The P1-5 fix through the real manager: a policy denial after
# reservation releases the confirmation, it is not burned.
# ---------------------------------------------------------------


class _SensitiveTool(BaseTool):
    name = "sensitive_tool"
    spec = ToolSpec(
        name="sensitive_tool",
        description="probe",
        max_risk=0.1,
        side_effectful=True,
        requires_confirmation=True,
    )

    def __init__(self) -> None:
        self.executed: list = []

    def execute_invocation(self, invocation):
        self.executed.append(invocation)
        return {"ok": True}

    def execute(self, input_data):  # pragma: no cover
        raise AssertionError("legacy path must not be used")


def _manager_with(reg):
    tools = ToolRegistry()
    tool = _SensitiveTool()
    tools.register(tool)
    return ToolManager(tools, ToolExecutor(tools), confirmation_registry=reg), tool


def _turn(manager, ctx, payload):
    decision = SimpleNamespace(tool="sensitive_tool", tool_payload=payload)
    result = SimpleNamespace(action_decision=decision)
    return manager.run(result, ctx)


def test_policy_denial_releases_the_confirmation_not_burns_it():
    reg = ConfirmationRegistry()
    payload = {"cmd": "go"}
    conf = reg.issue(tool_name="sensitive_tool", payload=payload, principal="u1")
    manager, tool = _manager_with(reg)

    # High turn risk exceeds the tool max_risk: policy denies AFTER the
    # confirmation was reserved.
    carrier = SimpleNamespace(confirmation_id=conf.confirmation_id)
    ctx_denied = SimpleNamespace(
        extra={"input_risk": 0.9},
        confirmation_result=carrier,
        user_id="u1",
    )
    res = _turn(manager, ctx_denied, payload)
    assert res is not None and res.success is False
    assert tool.executed == []  # the effect never ran

    # The confirmation was NOT burned: a later low-risk turn succeeds.
    ctx_ok = SimpleNamespace(
        extra={"input_risk": 0.0},
        confirmation_result=carrier,
        user_id="u1",
    )
    res_ok = _turn(manager, ctx_ok, payload)
    assert res_ok is not None
    assert len(tool.executed) == 1


def test_successful_effect_commits_the_confirmation():
    reg = ConfirmationRegistry()
    payload = {"cmd": "go"}
    conf = reg.issue(tool_name="sensitive_tool", payload=payload, principal="u1")
    manager, tool = _manager_with(reg)

    carrier = SimpleNamespace(confirmation_id=conf.confirmation_id)
    ctx = SimpleNamespace(
        extra={"input_risk": 0.0},
        confirmation_result=carrier,
        user_id="u1",
    )
    res = _turn(manager, ctx, payload)
    assert res is not None
    assert len(tool.executed) == 1
    # Committed: single use, gone from the pool.
    assert reg.pending_count() == 0
    # The authorization snapshot was threaded to the effect context.
    assert "tool_authorization_snapshot" in ctx.extra
    snap = ctx.extra["tool_authorization_snapshot"]
    assert snap["confirmed"] is True
    assert snap["confirmation_commitment"] == conf.payload_sha256
