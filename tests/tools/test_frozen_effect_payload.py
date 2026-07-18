"""Campaign 7 Lot 1: immutable, canonical tool payloads."""

from __future__ import annotations

import copy
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import PurePosixPath
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest

from arvis.adapters.tools.invocation import (
    FrozenEffectPayload,
    FrozenEffectPayloadError,
    ToolInvocation,
)
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.syscalls.engagement import stable_hash
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry, payload_commitment
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolAuthorizationOutcome, ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.runtime.runtime_bindings import resolve_process_id
from arvis.tools.spec import ToolSpec


class _Mode(Enum):
    SAFE = "safe"


class _RecordingTool(BaseTool):
    name = "frozen_probe"
    spec = ToolSpec(name="frozen_probe", description="frozen payload probe")

    def __init__(self) -> None:
        self.executed: list[dict[str, Any]] = []

    def execute(self, input_data: dict[str, Any]) -> Any:
        self.executed.append(copy.deepcopy(input_data["tool_payload"]))
        return {"ok": True}


def _result(payload: dict[str, Any]) -> Any:
    return SimpleNamespace(
        action_decision=SimpleNamespace(tool="frozen_probe", tool_payload=payload)
    )


def _ctx(*, confirmation_id: str | None = None) -> Any:
    confirmation_result = (
        SimpleNamespace(confirmation_id=confirmation_id)
        if confirmation_id is not None
        else None
    )
    return SimpleNamespace(
        extra={},
        user_id="u1",
        confirmation_result=confirmation_result,
    )


def _manager(
    tool: _RecordingTool,
    *,
    confirmation_registry: ConfirmationRegistry | None = None,
) -> ToolManager:
    registry = ToolRegistry()
    registry.register(tool)
    return ToolManager(
        registry,
        ToolExecutor(registry),
        confirmation_registry=confirmation_registry,
    )


def test_frozen_payload_materializations_share_no_mutable_reference() -> None:
    original = {
        "target": "A",
        "nested": {"value": 1},
        "items": [1, {"x": 2}],
        "buffer": bytearray(b"A"),
    }
    frozen = FrozenEffectPayload(original)

    first = frozen.materialize()
    second = frozen.materialize()
    first["nested"]["value"] = 9
    first["items"][1]["x"] = 8
    first["buffer"][0] = ord("Z")
    original["nested"]["value"] = 7
    original["items"].append(3)

    assert second == {
        "target": "A",
        "nested": {"value": 1},
        "items": [1, {"x": 2}],
        "buffer": bytearray(b"A"),
    }
    assert frozen.materialize() == second
    with pytest.raises(AttributeError, match="immutable"):
        frozen.sha256 = "forged"  # type: ignore[misc]


def test_frozen_payload_preserves_supported_canonical_types() -> None:
    payload = {
        "bytes": b"A",
        "bytearray": bytearray(b"B"),
        "date": date(2026, 7, 18),
        "datetime": datetime(2026, 7, 18, 12, 30, tzinfo=UTC),
        "decimal": Decimal("12.3400"),
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "path": PurePosixPath("/tmp/arvis"),
        "enum": _Mode.SAFE,
        "tuple": (1, "x"),
        "set": {1, 2},
        "frozenset": frozenset({"a", "b"}),
    }

    frozen = FrozenEffectPayload(payload)
    assert frozen.materialize() == payload
    assert len(frozen.sha256) == 64
    assert frozen.canonical_bytes


def test_non_isolating_deepcopy_is_refused() -> None:
    class _BadCopy:
        def __init__(self) -> None:
            self.value = 1

        def __deepcopy__(self, memo: dict[int, Any]) -> _BadCopy:
            return self

    with pytest.raises(FrozenEffectPayloadError, match="mutable references"):
        FrozenEffectPayload({"bad": _BadCopy()})


def test_tool_invocation_payload_property_returns_fresh_copies() -> None:
    invocation = ToolInvocation(
        tool_name="frozen_probe",
        payload={"nested": {"value": 1}},
        process_id="p1",
    )

    first = invocation.payload
    first["nested"]["value"] = 2

    assert invocation.payload == {"nested": {"value": 1}}
    assert invocation.payload_sha256 == invocation.frozen_payload.sha256
    assert (
        invocation.canonical_payload_bytes == invocation.frozen_payload.canonical_bytes
    )


def test_policy_cannot_mutate_future_effect_payload(monkeypatch: Any) -> None:
    tool = _RecordingTool()
    manager = _manager(tool)
    payload = {"target": "A", "nested": {"value": 1}}

    def _mutating_policy(invocation: ToolInvocation, registry: ToolRegistry) -> Any:
        del registry
        policy_copy = invocation.payload
        policy_copy["target"] = "B"
        policy_copy["nested"]["value"] = 2
        return SimpleNamespace(allowed=True, reason="allowed")

    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        staticmethod(_mutating_policy),
    )

    outcome = manager.authorize(_result(payload), _ctx())
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None
    manager.execute_authorized(outcome.authorized, _result(payload), _ctx())

    assert tool.executed == [{"target": "A", "nested": {"value": 1}}]


def test_tool_validation_cannot_mutate_execution_payload() -> None:
    class _MutatingValidatorTool(_RecordingTool):
        def validate(self, input_data: dict[str, Any]) -> None:
            input_data["tool_payload"]["target"] = "validator-mutated"
            input_data["tool_payload"]["nested"]["value"] = 99

    tool = _MutatingValidatorTool()
    manager = _manager(tool)
    payload = {"target": "A", "nested": {"value": 1}}

    result = manager.run(_result(payload), _ctx())

    assert result is not None and result.success is True
    assert tool.executed == [{"target": "A", "nested": {"value": 1}}]


def test_confirmation_and_idempotency_bind_frozen_payload() -> None:
    confirmations = ConfirmationRegistry()
    tool = _RecordingTool()
    manager = _manager(tool, confirmation_registry=confirmations)
    payload = {"target": "A", "nested": {"value": 1}}
    record = confirmations.issue(
        tool_name="frozen_probe",
        payload=payload,
        principal="u1",
    )
    ctx = _ctx(confirmation_id=record.confirmation_id)

    outcome = manager.authorize(_result(payload), ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None
    invocation = outcome.authorized.invocation

    payload["target"] = "B"
    payload["nested"]["value"] = 2

    frozen_material = invocation.materialize_payload()
    assert payload_commitment(frozen_material) == record.payload_sha256
    expected_idempotency = "idem:" + stable_hash(
        {
            "idempotency_version": 1,
            "tool": "frozen_probe",
            "payload_sha256": payload_commitment(frozen_material),
            "principal": "u1",
            "tenant": None,
            "process_id": resolve_process_id(ctx),
        }
    )
    assert invocation.idempotency_key == expected_idempotency


def test_confirmation_callback_cannot_change_idempotency_or_effect() -> None:
    class _MutatingConfirmationRegistry(ConfirmationRegistry):
        def reserve(
            self,
            *,
            confirmation_id: str,
            tool_name: str,
            payload: Any,
            principal: str | None,
            tenant: str | None = None,
        ):
            reserved = super().reserve(
                confirmation_id=confirmation_id,
                tool_name=tool_name,
                payload=copy.deepcopy(payload),
                principal=principal,
                tenant=tenant,
            )
            payload["target"] = "confirmation-mutated"
            return reserved

    confirmations = _MutatingConfirmationRegistry()
    tool = _RecordingTool()
    manager = _manager(tool, confirmation_registry=confirmations)
    payload = {"target": "A"}
    record = confirmations.issue(
        tool_name="frozen_probe",
        payload=payload,
        principal="u1",
    )
    ctx = _ctx(confirmation_id=record.confirmation_id)

    outcome = manager.authorize(_result(payload), ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None
    invocation = outcome.authorized.invocation
    expected_idempotency = "idem:" + stable_hash(
        {
            "idempotency_version": 1,
            "tool": "frozen_probe",
            "payload_sha256": payload_commitment({"target": "A"}),
            "principal": "u1",
            "tenant": None,
            "process_id": resolve_process_id(ctx),
        }
    )

    result = manager.execute_authorized(outcome.authorized, _result(payload), ctx)

    assert result is not None and result.success is True
    assert invocation.idempotency_key == expected_idempotency
    assert tool.executed == [{"target": "A"}]


def test_intent_and_execution_use_the_same_frozen_payload(monkeypatch: Any) -> None:
    tool = _RecordingTool()
    registry = ToolRegistry()
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(registry, executor)
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
        ),
    )
    payload = {"target": "A", "nested": {"value": 1}}
    result = _result(payload)
    ctx = _ctx()
    outcome = manager.authorize(result, ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None

    captured: list[dict[str, Any]] = []
    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    real_digest = handler_module.effect_engagement_digest

    def _capture(**kwargs: Any) -> str:
        captured.append(dict(kwargs["args"]["result"]))
        return real_digest(**kwargs)

    monkeypatch.setattr(handler_module, "effect_engagement_digest", _capture)

    payload["target"] = "B"
    payload["nested"]["value"] = 2
    syscall_result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": result,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )

    assert syscall_result.success is True
    assert captured == [
        {
            "tool": "frozen_probe",
            "tool_payload_sha256": outcome.authorized.payload_sha256,
        }
    ]
    assert tool.executed == [{"target": "A", "nested": {"value": 1}}]
