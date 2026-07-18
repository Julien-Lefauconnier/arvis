"""Campaign 7 Lot 5: exception-safe confirmation lifecycle."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import arvis.tools.manager as manager_module
from arvis.adapters.tools.authorization_snapshot import ToolAuthorizationSnapshot
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.tools.authorized_invocation import InvocationAuthority
from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec
from arvis.tools.tool_result import (
    EFFECT_COMPLETED,
    EFFECT_FAILED,
    EFFECT_NOT_STARTED,
    EFFECT_STARTED,
    EFFECT_STATE_UNKNOWN,
    PRE_EFFECT_REFUSAL,
    ToolEffectState,
    effect_has_started,
)


class _Tool(BaseTool):
    def __init__(
        self,
        *,
        required_consent: str | None = None,
        data_egress: bool = False,
        validate_raises: bool = False,
    ) -> None:
        self.name = "guarded"
        self.spec = ToolSpec(
            name="guarded",
            description="confirmation exception-safety probe",
            requires_confirmation=True,
            required_consent=required_consent,
            data_egress=data_egress,
            provider="external" if data_egress else None,
        )
        self.validate_raises = validate_raises
        self.executions = 0

    def validate(self, input_data: dict[str, Any]) -> None:
        if self.validate_raises:
            raise RuntimeError("validation exploded")

    def execute(self, input_data: dict[str, Any]) -> Any:
        self.executions += 1
        return {"ok": True}


class _AllowConsent:
    def is_granted(self, invocation: Any, consent_key: str) -> bool:
        return True


class _BoomConsent:
    def is_granted(self, invocation: Any, consent_key: str) -> bool:
        raise RuntimeError("consent exploded")


class _BoomEgress:
    def is_allowed(self, invocation: Any, spec: ToolSpec) -> bool:
        raise RuntimeError("egress exploded")


def _rig(
    *,
    tool: _Tool | None = None,
    consent_gate: Any = None,
    egress_gate: Any = None,
) -> tuple[ToolManager, ConfirmationRegistry, _Tool]:
    registry = ToolRegistry()
    installed = tool or _Tool()
    registry.register(installed)
    confirmations = ConfirmationRegistry()
    manager = ToolManager(
        registry,
        ToolExecutor(registry),
        confirmation_registry=confirmations,
        consent_gate=consent_gate,
        egress_gate=egress_gate,
        require_gates=consent_gate is not None or egress_gate is not None,
    )
    return manager, confirmations, installed


def _result(payload: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        action_decision=SimpleNamespace(tool="guarded", tool_payload=payload)
    )


def _context(confirmation_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        extra={"input_risk": 0.0},
        confirmation_result=SimpleNamespace(confirmation_id=confirmation_id),
        consent_granted=("publish",),
        user_id="u1",
    )


def _issue(confirmations: ConfirmationRegistry, payload: dict[str, Any]) -> str:
    return confirmations.issue(
        tool_name="guarded",
        payload=payload,
        principal="u1",
        tenant=None,
    ).confirmation_id


def _assert_reservable_again(
    confirmations: ConfirmationRegistry,
    confirmation_id: str,
    payload: dict[str, Any],
) -> None:
    reserved = confirmations.reserve(
        confirmation_id=confirmation_id,
        tool_name="guarded",
        payload=payload,
        principal="u1",
        tenant=None,
    )
    assert reserved is not None
    assert confirmations.release(confirmation_id=confirmation_id) is True


def test_reservation_context_releases_on_exception() -> None:
    confirmations = ConfirmationRegistry()
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)

    with pytest.raises(RuntimeError, match="boom"):
        with confirmations.reserve_transaction(
            confirmation_id=confirmation_id,
            tool_name="guarded",
            payload=payload,
            principal="u1",
        ) as reservation:
            assert reservation.confirmation is not None
            raise RuntimeError("boom")

    _assert_reservable_again(confirmations, confirmation_id, payload)


def test_handoff_keeps_reservation_until_explicit_effect_finalization() -> None:
    confirmations = ConfirmationRegistry()
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)

    with confirmations.reserve_transaction(
        confirmation_id=confirmation_id,
        tool_name="guarded",
        payload=payload,
        principal="u1",
    ) as reservation:
        reservation.handoff()

    assert reservation.handed_off is True
    assert reservation.closed is False
    assert (
        confirmations.reserve(
            confirmation_id=confirmation_id,
            tool_name="guarded",
            payload=payload,
            principal="u1",
        )
        is None
    )
    assert reservation.commit_after_effect(EFFECT_NOT_STARTED) is True
    _assert_reservable_again(confirmations, confirmation_id, payload)


@pytest.mark.parametrize(
    ("state", "spent"),
    [
        (PRE_EFFECT_REFUSAL, False),
        (EFFECT_NOT_STARTED, False),
        (EFFECT_STARTED, True),
        (EFFECT_COMPLETED, True),
        (EFFECT_FAILED, True),
        (EFFECT_STATE_UNKNOWN, True),
        ("foreign_state", True),
    ],
)
def test_effect_states_drive_confirmation_finalization(
    state: ToolEffectState | str,
    spent: bool,
) -> None:
    confirmations = ConfirmationRegistry()
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)
    reservation = confirmations.reserve_transaction(
        confirmation_id=confirmation_id,
        tool_name="guarded",
        payload=payload,
        principal="u1",
    )
    reservation.handoff()

    assert effect_has_started(state) is spent
    assert reservation.commit_after_effect(state) is True
    assert confirmations.pending_count() == (0 if spent else 1)


@pytest.mark.parametrize(
    "failure_point",
    [
        "canonicalizer",
        "tool_policy",
        "snapshot_builder",
        "capability_mint",
        "consent_gate",
        "egress_gate",
    ],
)
def test_authorization_exception_releases_reserved_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    required_consent = (
        "publish" if failure_point in {"consent_gate", "egress_gate"} else None
    )
    data_egress = failure_point == "egress_gate"
    consent_gate: Any = None
    egress_gate: Any = None
    if failure_point == "consent_gate":
        consent_gate = _BoomConsent()
    elif failure_point == "egress_gate":
        consent_gate = _AllowConsent()
        egress_gate = _BoomEgress()

    manager, confirmations, _tool = _rig(
        tool=_Tool(
            required_consent=required_consent,
            data_egress=data_egress,
        ),
        consent_gate=consent_gate,
        egress_gate=egress_gate,
    )
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)

    def _boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"{failure_point} exploded")

    if failure_point == "canonicalizer":
        monkeypatch.setattr(manager_module, "payload_commitment", _boom)
    elif failure_point == "tool_policy":
        monkeypatch.setattr(ToolPolicyEvaluator, "evaluate", staticmethod(_boom))
    elif failure_point == "snapshot_builder":
        monkeypatch.setattr(ToolAuthorizationSnapshot, "to_material", _boom)
    elif failure_point == "capability_mint":
        monkeypatch.setattr(InvocationAuthority, "mint", _boom)

    with pytest.raises(RuntimeError, match="exploded"):
        manager.authorize(_result(payload), _context(confirmation_id))

    _assert_reservable_again(confirmations, confirmation_id, payload)


def test_executor_validation_exception_is_effect_not_started_and_releases() -> None:
    manager, confirmations, tool = _rig(tool=_Tool(validate_raises=True))
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)

    result = manager.run(_result(payload), _context(confirmation_id))

    assert result is not None
    assert result.success is False
    assert result.effect_boundary == EFFECT_NOT_STARTED
    assert tool.executions == 0
    _assert_reservable_again(confirmations, confirmation_id, payload)


def test_local_outbox_exception_revokes_and_releases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, confirmations, tool = _rig()
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)

    class _FailingSink:
        def append(self, intent: dict[str, Any]) -> Any:
            raise RuntimeError("outbox exploded")

    monkeypatch.setattr(manager_module, "InMemoryAuditSink", _FailingSink)

    with pytest.raises(RuntimeError, match="outbox exploded"):
        manager.run(_result(payload), _context(confirmation_id))

    assert tool.executions == 0
    _assert_reservable_again(confirmations, confirmation_id, payload)


def test_forged_capability_cannot_release_another_capability_reservation() -> None:
    from dataclasses import replace

    from arvis.tools.authorized_invocation import UnauthorizedExecutionError

    manager, confirmations, _tool = _rig()
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)
    outcome = manager.authorize(_result(payload), _context(confirmation_id))
    assert outcome is not None and outcome.authorized is not None

    forged = replace(outcome.authorized, nonce="forged-nonce")
    with pytest.raises(UnauthorizedExecutionError):
        manager.execute_authorized(forged, _result(payload), _context(confirmation_id))

    # The legitimate capability still owns the locked reservation.
    assert (
        confirmations.reserve(
            confirmation_id=confirmation_id,
            tool_name="guarded",
            payload=payload,
            principal="u1",
        )
        is None
    )
    assert manager.abort_authorized(outcome.authorized) is True
    _assert_reservable_again(confirmations, confirmation_id, payload)


def test_unexpected_executor_exception_releases_and_revokes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, confirmations, _tool = _rig()
    payload = {"x": 1}
    confirmation_id = _issue(confirmations, payload)

    def _boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("executor exploded before effect")

    monkeypatch.setattr(manager.executor, "execute_invocation", _boom)

    with pytest.raises(RuntimeError, match="executor exploded before effect"):
        manager.run(_result(payload), _context(confirmation_id))

    _assert_reservable_again(confirmations, confirmation_id, payload)
