"""Campaign 8 red tests for effect-context and enum integrity gaps.

The pending findings are strict xfails: they reproduce the vulnerable
behaviour without breaking the historical gate, while an unexpected pass is
itself a failure until the corresponding marker is deliberately removed.
"""

from __future__ import annotations

from enum import IntEnum, IntFlag, StrEnum
from types import SimpleNamespace
from typing import Any

import pytest

from arvis.kernel_core.access.models import AuthenticatedPrincipal
from arvis.kernel_core.canonicalization import canonical_hash
from arvis.kernel_core.syscalls.audit_sink import InMemoryAuditSink
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.authorized_invocation import CapabilityState
from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolAuthorizationOutcome, ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _StringOperation(StrEnum):
    DELETE = "delete"


class _IntegerOperation(IntEnum):
    ONE = 1


class _Permission(IntFlag):
    READ = 1
    WRITE = 2


class _RecordingTool(BaseTool):
    def __init__(self, *, requires_confirmation: bool = False) -> None:
        self.name = "campaign8_probe"
        self.spec = ToolSpec(
            name=self.name,
            description="campaign 8 effect-context probe",
            requires_confirmation=requires_confirmation,
        )
        self.calls: list[dict[str, Any]] = []

    def execute(self, input_data: dict[str, Any]) -> Any:
        self.calls.append(dict(input_data.get("tool_payload", {})))
        return {"ok": True}


def _principal(
    user_id: str,
    *,
    tenant: str = "tenant-a",
    source: str = "oidc",
    strength: str = "mfa",
    service_id: str = "service-a",
    session_id_hash: str = "sha256:session-a",
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user_id,
        organization_id=tenant,
        authentication_source=source,
        authentication_strength=strength,
        service_id=service_id,
        session_id_hash=session_id_hash,
    )


def _ctx(
    principal: AuthenticatedPrincipal,
    *,
    confirmation_id: str | None = None,
) -> Any:
    confirmation_result = (
        SimpleNamespace(confirmation_id=confirmation_id)
        if confirmation_id is not None
        else None
    )
    return SimpleNamespace(
        extra={},
        user_id=principal.user_id,
        principal=principal,
        confirmation_result=confirmation_result,
    )


def _result(payload: dict[str, Any] | None = None) -> Any:
    return SimpleNamespace(
        action_decision=SimpleNamespace(
            tool="campaign8_probe",
            tool_payload=payload or {"target": "record-a"},
        )
    )


def _rig(
    *,
    requires_confirmation: bool = False,
    confirmation_registry: ConfirmationRegistry | None = None,
) -> tuple[_RecordingTool, ToolManager, SyscallHandler]:
    registry = ToolRegistry()
    tool = _RecordingTool(requires_confirmation=requires_confirmation)
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
            audit_intent_sink=InMemoryAuditSink(),
            require_authenticated_principal=True,
        ),
    )
    return tool, manager, handler


def _authorize(manager: ToolManager, result: Any, ctx: Any) -> ToolAuthorizationOutcome:
    outcome = manager.authorize(result, ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None
    return outcome


def _handle(
    handler: SyscallHandler,
    result: Any,
    ctx: Any,
    outcome: ToolAuthorizationOutcome,
) -> Any:
    return handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": result,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "campaign 8: a mutable authorization context still crosses the effect boundary"
    ),
)
def test_context_identity_mutation_after_authorization_is_refused() -> None:
    confirmations = ConfirmationRegistry()
    tool, manager, handler = _rig(
        requires_confirmation=True,
        confirmation_registry=confirmations,
    )
    payload = {"target": "record-a"}
    confirmation = confirmations.issue(
        tool_name="campaign8_probe",
        payload=payload,
        principal="alice",
        tenant="tenant-a",
    )
    ctx = _ctx(
        _principal("alice"),
        confirmation_id=confirmation.confirmation_id,
    )
    result = _result(payload)
    outcome = _authorize(manager, result, ctx)

    ctx.user_id = "bob"
    ctx.principal = _principal("bob")
    refused = _handle(handler, result, ctx, outcome)

    assert refused.success is False
    assert tool.calls == []
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED
    assert confirmations.pending_count() == 1
    assert ctx.extra.get("syscall_intents", []) == []


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: a capability can still be presented from a distinct context",
)
def test_alice_capability_cannot_be_presented_in_bob_context() -> None:
    tool, manager, handler = _rig()
    alice_ctx = _ctx(_principal("alice"))
    bob_ctx = _ctx(_principal("bob"))
    result = _result()
    outcome = _authorize(manager, result, alice_ctx)

    refused = _handle(handler, result, bob_ctx, outcome)

    assert refused.success is False
    assert tool.calls == []
    assert manager.capability_state(outcome.authorized) is CapabilityState.REVOKED
    assert bob_ctx.extra.get("syscall_intents", []) == []


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: tenant binding is not compared with the sealed authorization",
)
def test_tenant_mutation_after_authorization_is_refused() -> None:
    tool, manager, handler = _rig()
    ctx = _ctx(_principal("alice", tenant="tenant-a"))
    result = _result()
    outcome = _authorize(manager, result, ctx)

    ctx.principal = _principal("alice", tenant="tenant-b")
    refused = _handle(handler, result, ctx, outcome)

    assert refused.success is False
    assert tool.calls == []
    assert ctx.extra.get("syscall_intents", []) == []


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: session binding is not compared with the sealed authorization",
)
def test_session_binding_mutation_after_authorization_is_refused() -> None:
    tool, manager, handler = _rig()
    ctx = _ctx(_principal("alice", session_id_hash="sha256:session-a"))
    result = _result()
    outcome = _authorize(manager, result, ctx)

    ctx.principal = _principal("alice", session_id_hash="sha256:session-b")
    refused = _handle(handler, result, ctx, outcome)

    assert refused.success is False
    assert tool.calls == []
    assert ctx.extra.get("syscall_intents", []) == []


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: service binding is not compared with the sealed authorization",
)
def test_service_identity_mutation_after_authorization_is_refused() -> None:
    tool, manager, handler = _rig()
    ctx = _ctx(_principal("alice", service_id="service-a"))
    result = _result()
    outcome = _authorize(manager, result, ctx)

    ctx.principal = _principal("alice", service_id="service-b")
    refused = _handle(handler, result, ctx, outcome)

    assert refused.success is False
    assert tool.calls == []
    assert ctx.extra.get("syscall_intents", []) == []


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: StrEnum is dispatched as its str parent",
)
def test_strenum_does_not_alias_raw_string() -> None:
    assert canonical_hash(_StringOperation.DELETE) != canonical_hash("delete")


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: IntEnum is dispatched as its int parent",
)
def test_intenum_does_not_alias_raw_integer() -> None:
    assert canonical_hash(_IntegerOperation.ONE) != canonical_hash(1)


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: IntFlag is dispatched as its int parent",
)
def test_intflag_does_not_alias_raw_integer() -> None:
    combined = _Permission.READ | _Permission.WRITE
    assert canonical_hash(combined) != canonical_hash(3)


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: enum mapping keys are encoded as scalar keys",
)
def test_enum_mapping_key_does_not_alias_scalar_key() -> None:
    enum_keyed = {_StringOperation.DELETE: {"target": "record-a"}}
    scalar_keyed = {"delete": {"target": "record-a"}}
    assert canonical_hash(enum_keyed) != canonical_hash(scalar_keyed)


@pytest.mark.xfail(
    strict=True,
    reason="campaign 8: enum and scalar payloads still share confirmation material",
)
def test_confirmation_distinguishes_enum_payload_from_scalar_payload() -> None:
    registry = ConfirmationRegistry()
    confirmation = registry.issue(
        tool_name="campaign8_probe",
        payload={"operation": _StringOperation.DELETE},
        principal="alice",
        tenant="tenant-a",
    )

    reservation = registry.reserve(
        confirmation_id=confirmation.confirmation_id,
        tool_name="campaign8_probe",
        payload={"operation": "delete"},
        principal="alice",
        tenant="tenant-a",
    )

    assert reservation is None
    assert registry.pending_count() == 1
