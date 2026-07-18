"""Receipt-bound transaction for effectful tool capabilities (campaign 7 Lot 4)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import Any

import pytest

from arvis.kernel_core.syscalls.audit_sink import AuditReceipt, InMemoryAuditSink
from arvis.kernel_core.syscalls.intent_result_bijection import (
    verify_intent_result_bijection,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.authorized_invocation import (
    CapabilityState,
    UnauthorizedExecutionError,
)
from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolAuthorizationOutcome, ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _Tool(BaseTool):
    def __init__(self, *, requires_confirmation: bool = False) -> None:
        self.name = "transaction_probe"
        self.spec = ToolSpec(
            name=self.name,
            description="receipt transaction probe",
            requires_confirmation=requires_confirmation,
        )
        self.calls: list[dict[str, Any]] = []

    def execute(self, input_data: dict[str, Any]) -> Any:
        payload = dict(input_data.get("tool_payload", {}))
        self.calls.append(payload)
        return {"ok": True}


def _result(payload: dict[str, Any] | None = None) -> Any:
    return SimpleNamespace(
        action_decision=SimpleNamespace(
            tool="transaction_probe",
            tool_payload=payload or {"value": 1},
        )
    )


def _ctx(*, confirmation_id: str | None = None) -> Any:
    confirmation = (
        SimpleNamespace(confirmation_id=confirmation_id)
        if confirmation_id is not None
        else None
    )
    return SimpleNamespace(
        extra={},
        user_id="u1",
        confirmation_result=confirmation,
    )


def _rig(
    *,
    sink: Any | None = None,
    require_sink: bool = False,
    confirmation_registry: ConfirmationRegistry | None = None,
    requires_confirmation: bool = False,
) -> tuple[_Tool, ToolManager, SyscallHandler]:
    registry = ToolRegistry()
    tool = _Tool(requires_confirmation=requires_confirmation)
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(
        registry,
        executor,
        confirmation_registry=confirmation_registry,
    )
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
            audit_intent_sink=sink,
            require_durable_intent_sink=require_sink,
        ),
    )
    return tool, manager, handler


def _authorize(
    manager: ToolManager,
    result: Any,
    ctx: Any,
) -> ToolAuthorizationOutcome:
    outcome = manager.authorize(result, ctx)
    assert type(outcome) is ToolAuthorizationOutcome
    assert outcome.authorized is not None
    return outcome


def _receipt(
    *,
    receipt_id: str = "receipt-1",
    intent_sha256: str = "a" * 64,
    run_id: str | None = "run-1",
    causal_id: str = "causal-1",
) -> AuditReceipt:
    return AuditReceipt(
        receipt_id=receipt_id,
        run_id=run_id,
        causal_id=causal_id,
        intent_sha256=intent_sha256,
        durable_position="42",
        store_fingerprint="db:test",
        committed_at="2026-07-19T00:00:00+00:00",
    )


def _activate(
    manager: ToolManager,
    outcome: ToolAuthorizationOutcome,
    *,
    receipt: AuditReceipt | None = None,
    intent_sha256: str = "a" * 64,
    run_id: str | None = "run-1",
    causal_id: str = "causal-1",
) -> bool:
    assert outcome.authorized is not None
    acknowledgement = receipt or _receipt(
        intent_sha256=intent_sha256,
        run_id=run_id,
        causal_id=causal_id,
    )
    return manager.activate_authorized(
        outcome.authorized,
        receipt=acknowledgement,
        intent_sha256=intent_sha256,
        run_id=run_id,
        causal_id=causal_id,
    )


def test_capability_cannot_execute_before_receipt_activation() -> None:
    tool, manager, _handler = _rig()
    ctx = _ctx()
    result = _result()
    outcome = _authorize(manager, result, ctx)
    assert outcome.authorized is not None
    assert manager.capability_state(outcome.authorized) is CapabilityState.MINTED

    with pytest.raises(UnauthorizedExecutionError):
        manager.execute_authorized(outcome.authorized, result, ctx)

    assert tool.calls == []
    assert manager.capability_state(outcome.authorized) is CapabilityState.MINTED


def test_valid_handler_receipt_activates_then_consumes_capability() -> None:
    sink = InMemoryAuditSink()
    tool, manager, handler = _rig(sink=sink)
    ctx = _ctx()
    result = _result({"value": 7})
    outcome = _authorize(manager, result, ctx)
    assert outcome.authorized is not None

    syscall_result = handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": result, "ctx": ctx, "authorization": outcome},
        )
    )

    assert syscall_result.success is True
    assert tool.calls == [{"value": 7}]
    assert manager.capability_state(outcome.authorized) is CapabilityState.CONSUMED
    activation = manager.capability_activation(outcome.authorized)
    assert activation is not None
    assert activation.receipt_id == sink.receipts[0].receipt_id
    assert activation.intent_sha256 == sink.receipts[0].intent_sha256
    assert activation.causal_id == sink.receipts[0].causal_id


def test_sink_exception_revokes_capability_and_prevents_effect() -> None:
    class _RaisingSink:
        def append(self, intent: dict[str, Any]) -> AuditReceipt:
            raise OSError("store unavailable")

    tool, manager, handler = _rig(sink=_RaisingSink(), require_sink=True)
    ctx = _ctx()
    result = _result()
    outcome = _authorize(manager, result, ctx)
    assert outcome.authorized is not None

    refused = handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": result, "ctx": ctx, "authorization": outcome},
        )
    )

    assert refused.success is False
    assert tool.calls == []
    assert ctx.extra.get("syscall_intents", []) == []
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED
    with pytest.raises(UnauthorizedExecutionError):
        manager.execute_authorized(outcome.authorized, result, ctx)


def test_receipt_replay_refusal_closes_the_accepted_intent() -> None:
    class _ReusedReceiptIdSink:
        def append(self, intent: dict[str, Any]) -> AuditReceipt:
            return AuditReceipt(
                receipt_id="receipt-replayed",
                run_id=intent.get("run_id"),
                causal_id=str(intent.get("causal_id", "")),
                intent_sha256=str(intent.get("commitment_sha256", "")),
                durable_position=str(intent.get("causal_id", "")),
                store_fingerprint="db:test",
                committed_at="2026-07-19T00:00:00+00:00",
            )

    tool, manager, handler = _rig(sink=_ReusedReceiptIdSink())
    ctx = _ctx()
    result = _result()
    first = _authorize(manager, result, ctx)
    second = _authorize(manager, result, ctx)
    assert first.authorized is not None
    assert second.authorized is not None

    first_result = handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": result, "ctx": ctx, "authorization": first},
        )
    )
    second_result = handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": result, "ctx": ctx, "authorization": second},
        )
    )

    assert first_result.success is True
    assert second_result.success is False
    assert tool.calls == [{"value": 1}]
    assert manager.capability_state(first.authorized) is CapabilityState.CONSUMED
    assert manager.capability_state(second.authorized) is CapabilityState.REVOKED
    intents = ctx.extra["syscall_intents"]
    results = ctx.extra["syscall_results"]
    assert len(intents) == len(results) == 2
    assert verify_intent_result_bijection(intents, results).ok is True


def test_sink_failure_releases_reserved_confirmation() -> None:
    class _RaisingSink:
        def append(self, intent: dict[str, Any]) -> AuditReceipt:
            raise OSError("store unavailable")

    confirmations = ConfirmationRegistry()
    payload = {"value": 9}
    record = confirmations.issue(
        tool_name="transaction_probe",
        payload=payload,
        principal="u1",
        tenant=None,
    )
    tool, manager, handler = _rig(
        sink=_RaisingSink(),
        require_sink=True,
        confirmation_registry=confirmations,
        requires_confirmation=True,
    )
    ctx = _ctx(confirmation_id=record.confirmation_id)
    result = _result(payload)
    outcome = _authorize(manager, result, ctx)
    assert outcome.authorized is not None

    refused = handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": result, "ctx": ctx, "authorization": outcome},
        )
    )

    assert refused.success is False
    assert tool.calls == []
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED
    reserved_again = confirmations.reserve(
        confirmation_id=record.confirmation_id,
        tool_name="transaction_probe",
        payload=payload,
        principal="u1",
        tenant=None,
    )
    assert reserved_again == record


def test_aborted_capability_cannot_be_activated() -> None:
    _tool, manager, _handler = _rig()
    ctx = _ctx()
    result = _result()
    outcome = _authorize(manager, result, ctx)
    assert outcome.authorized is not None

    assert manager.abort_authorized(outcome.authorized) is True
    assert _activate(manager, outcome) is False
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED


def test_activation_binds_the_exact_receipt_idempotently() -> None:
    _tool, manager, _handler = _rig()
    outcome = _authorize(manager, _result(), _ctx())
    assert outcome.authorized is not None
    receipt = _receipt()

    assert _activate(manager, outcome, receipt=receipt) is True
    assert _activate(manager, outcome, receipt=receipt) is True
    activation = manager.capability_activation(outcome.authorized)
    assert activation is not None
    assert activation.receipt_id == receipt.receipt_id
    assert activation.intent_sha256 == receipt.intent_sha256
    assert activation.run_id == receipt.run_id
    assert activation.causal_id == receipt.causal_id


def test_receipt_for_other_run_revokes_capability() -> None:
    _tool, manager, _handler = _rig()
    outcome = _authorize(manager, _result(), _ctx())
    wrong = _receipt(run_id="run-other")

    assert _activate(manager, outcome, receipt=wrong, run_id="run-1") is False
    assert outcome.authorized is not None
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED


def test_receipt_for_other_intent_revokes_capability() -> None:
    _tool, manager, _handler = _rig()
    outcome = _authorize(manager, _result(), _ctx())
    wrong = _receipt(intent_sha256="b" * 64)

    assert _activate(manager, outcome, receipt=wrong, intent_sha256="a" * 64) is False
    assert outcome.authorized is not None
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED


def test_receipt_for_other_causal_id_revokes_capability() -> None:
    _tool, manager, _handler = _rig()
    outcome = _authorize(manager, _result(), _ctx())
    wrong = _receipt(causal_id="causal-other")

    assert _activate(manager, outcome, receipt=wrong, causal_id="causal-1") is False
    assert outcome.authorized is not None
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED


def test_one_receipt_cannot_activate_two_capabilities() -> None:
    _tool, manager, _handler = _rig()
    ctx = _ctx()
    result = _result()
    first = _authorize(manager, result, ctx)
    second = _authorize(manager, result, ctx)
    receipt = _receipt()

    assert _activate(manager, first, receipt=receipt) is True
    assert _activate(manager, second, receipt=receipt) is False
    assert first.authorized is not None
    assert second.authorized is not None
    assert manager.capability_state(first.authorized) is CapabilityState.ACTIVATED
    assert manager.capability_state(second.authorized) is CapabilityState.REVOKED


def test_concurrent_receipt_replay_has_exactly_one_winner() -> None:
    _tool, manager, _handler = _rig()
    ctx = _ctx()
    result = _result()
    outcomes = [_authorize(manager, result, ctx) for _ in range(32)]
    receipt = _receipt()

    with ThreadPoolExecutor(max_workers=16) as pool:
        outcomes_result = list(
            pool.map(
                lambda outcome: _activate(manager, outcome, receipt=receipt), outcomes
            )
        )

    assert outcomes_result.count(True) == 1
    states = [
        manager.capability_state(outcome.authorized)
        for outcome in outcomes
        if outcome.authorized is not None
    ]
    assert states.count(CapabilityState.ACTIVATED) == 1
    assert states.count(CapabilityState.REVOKED) == 31
