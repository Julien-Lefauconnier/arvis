"""Campaign 7 Lot 7: durable idempotency identity on the effect path."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.syscalls.audit_sink import InMemoryAuditSink
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolAuthorizationOutcome, ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _StructuredProbe(BaseTool):
    name = "idempotency_probe"
    spec = ToolSpec(
        name="idempotency_probe",
        description="idempotency probe",
        idempotent=True,
        retryable=True,
    )

    def __init__(self) -> None:
        self.keys: list[str | None] = []

    def execute(self, input_data: dict[str, Any]) -> Any:  # pragma: no cover
        raise AssertionError("structured path expected")

    def execute_invocation(self, invocation: ToolInvocation) -> Any:
        self.keys.append(invocation.idempotency_key)
        return {"ok": True}


class _LegacyProbe(BaseTool):
    name = "legacy_idempotency_probe"
    spec = ToolSpec(
        name="legacy_idempotency_probe",
        description="legacy idempotency probe",
        idempotent=True,
    )

    def __init__(self) -> None:
        self.keys: list[str | None] = []

    def execute(self, input_data: dict[str, Any]) -> Any:
        self.keys.append(input_data.get("idempotency_key"))
        return {"ok": True}


def _rig(monkeypatch, tool: BaseTool):
    registry = ToolRegistry()
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(registry=registry, executor=executor)
    sink = InMemoryAuditSink()
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
            audit_intent_sink=sink,
        ),
    )
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        staticmethod(
            lambda invocation, reg, **kwargs: SimpleNamespace(
                allowed=True,
                reason="allowed",
            )
        ),
    )
    return manager, handler, sink


def _authorize(
    manager: ToolManager,
    *,
    tool_name: str,
    payload: dict[str, Any],
    user_id: str = "u1",
):
    ctx = SimpleNamespace(extra={}, user_id=user_id)
    result = SimpleNamespace(
        action_decision=SimpleNamespace(tool=tool_name, tool_payload=payload)
    )
    outcome = manager.authorize(result, ctx)
    assert type(outcome) is ToolAuthorizationOutcome
    assert outcome.authorized is not None
    return ctx, result, outcome


def _execute(handler, ctx, result, outcome):
    return handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": result, "ctx": ctx, "authorization": outcome},
        )
    )


def test_idempotency_key_is_persisted_bound_and_delivered(monkeypatch) -> None:
    tool = _StructuredProbe()
    manager, handler, sink = _rig(monkeypatch, tool)
    ctx, result, outcome = _authorize(
        manager,
        tool_name=tool.name,
        payload={"target": "A"},
    )
    assert outcome.authorized is not None
    key = outcome.authorized.invocation.idempotency_key
    assert isinstance(key, str) and key.startswith("idem:")

    executed = _execute(handler, ctx, result, outcome)

    assert executed.success is True
    intent = ctx.extra["syscall_intents"][0]
    assert intent["idempotency_key"] == key
    assert sink.entries[0]["idempotency_key"] == key
    assert sink.receipts[0].intent_sha256 == intent["commitment_sha256"]
    assert tool.keys == [key]
    activation = manager.capability_activation(outcome.authorized)
    assert activation is not None
    assert activation.idempotency_key == key


def test_legacy_adapter_receives_the_authorized_idempotency_key(monkeypatch) -> None:
    tool = _LegacyProbe()
    manager, handler, _sink = _rig(monkeypatch, tool)
    ctx, result, outcome = _authorize(
        manager,
        tool_name=tool.name,
        payload={"target": "A"},
    )
    assert outcome.authorized is not None
    key = outcome.authorized.invocation.idempotency_key

    assert _execute(handler, ctx, result, outcome).success is True
    assert tool.keys == [key]


def test_same_logical_action_reuses_the_same_key(monkeypatch) -> None:
    manager, _handler, _sink = _rig(monkeypatch, _StructuredProbe())
    first = _authorize(
        manager,
        tool_name="idempotency_probe",
        payload={"target": "A"},
    )[2]
    second = _authorize(
        manager,
        tool_name="idempotency_probe",
        payload={"target": "A"},
    )[2]
    assert first.authorized is not None
    assert second.authorized is not None
    assert (
        first.authorized.invocation.idempotency_key
        == second.authorized.invocation.idempotency_key
    )


def test_payload_and_principal_select_distinct_keys(monkeypatch) -> None:
    manager, _handler, _sink = _rig(monkeypatch, _StructuredProbe())
    base = _authorize(
        manager,
        tool_name="idempotency_probe",
        payload={"target": "A"},
        user_id="u1",
    )[2]
    other_payload = _authorize(
        manager,
        tool_name="idempotency_probe",
        payload={"target": "B"},
        user_id="u1",
    )[2]
    other_principal = _authorize(
        manager,
        tool_name="idempotency_probe",
        payload={"target": "A"},
        user_id="u2",
    )[2]
    assert base.authorized is not None
    assert other_payload.authorized is not None
    assert other_principal.authorized is not None
    base_key = base.authorized.invocation.idempotency_key
    assert other_payload.authorized.invocation.idempotency_key != base_key
    assert other_principal.authorized.invocation.idempotency_key != base_key


def test_idempotency_key_changes_the_intent_commitment(monkeypatch) -> None:
    from arvis.tools import manager as manager_module

    tool = _StructuredProbe()
    manager, handler, _sink = _rig(monkeypatch, tool)
    hashes = iter(("a" * 64, "b" * 64))
    monkeypatch.setattr(manager_module, "stable_hash", lambda material: next(hashes))

    commitments: list[str] = []
    keys: list[str | None] = []
    for _ in range(2):
        ctx, result, outcome = _authorize(
            manager,
            tool_name=tool.name,
            payload={"target": "same"},
        )
        assert outcome.authorized is not None
        keys.append(outcome.authorized.invocation.idempotency_key)
        assert _execute(handler, ctx, result, outcome).success is True
        commitments.append(ctx.extra["syscall_intents"][0]["commitment_sha256"])

    assert keys == [f"idem:{'a' * 64}", f"idem:{'b' * 64}"]
    assert commitments[0] != commitments[1]


def test_persisted_key_can_be_restored_after_a_crash(monkeypatch) -> None:
    tool = _StructuredProbe()
    manager, handler, sink = _rig(monkeypatch, tool)
    payload = {"target": "A"}
    ctx, result, outcome = _authorize(
        manager,
        tool_name=tool.name,
        payload=payload,
    )
    assert outcome.authorized is not None
    original = outcome.authorized.invocation
    assert _execute(handler, ctx, result, outcome).success is True

    persisted = dict(sink.entries[0])
    recovered = ToolInvocation(
        tool_name=original.tool_name,
        payload=payload,
        process_id=original.process_id,
        user_id=original.user_id,
        principal=original.principal,
        tenant=original.tenant,
        idempotency_key=str(persisted["idempotency_key"]),
    )
    assert recovered.idempotency_key == original.idempotency_key
    assert recovered.idempotency_key == tool.keys[0]
