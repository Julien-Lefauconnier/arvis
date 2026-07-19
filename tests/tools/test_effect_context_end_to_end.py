"""End-to-end integrity of the sealed tool effect context (campaign 8)."""

from __future__ import annotations

import gc
import weakref
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace
from typing import Any

import pytest

import arvis.kernel_core.syscalls.syscall_handler as syscall_handler_module
from arvis.api.commitment import syscall_pair_commitments
from arvis.kernel_core.access.models import AuthenticatedPrincipal
from arvis.kernel_core.canonicalization import canonical_hash
from arvis.kernel_core.syscalls.audit_sink import InMemoryAuditSink
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.effect_context import (
    EFFECT_CONTEXT_FORMAT_VERSION,
    AuthorizedEffectContext,
)
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolAuthorizationOutcome, ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _RuntimeContext:
    """Weak-referenceable stand-in for the mutable pipeline context."""

    def __init__(
        self,
        principal: AuthenticatedPrincipal,
        *,
        process_id: str = "process-a",
        run_id: str = "run-a",
    ) -> None:
        self.extra: dict[str, Any] = {}
        self.user_id = principal.user_id
        self.principal = principal
        self.runtime_bindings = SimpleNamespace(
            process_id=process_id,
            run_id=run_id,
        )
        self.confirmation_result = None


class _ContextProbe(BaseTool):
    name = "effect_context_probe"
    spec = ToolSpec(name=name, description="sealed effect-context probe")

    def __init__(self) -> None:
        self.observed: list[AuthorizedEffectContext] = []

    def execute_invocation(self, invocation: Any) -> Any:
        self.observed.append(invocation.effect_context)
        return {"observed": invocation.effect_context.to_material()}

    def execute(self, input_data: dict[str, Any]) -> Any:  # pragma: no cover
        raise AssertionError("the structured invocation path must be used")


def _principal(
    *,
    user_id: str = "alice",
    tenant: str = "tenant-a",
    service_id: str = "document-service",
    session_id_hash: str = "sha256:session-a",
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user_id,
        organization_id=tenant,
        authentication_source="oidc",
        authentication_strength="hardware-key",
        service_id=service_id,
        session_id_hash=session_id_hash,
    )


def _rig() -> tuple[_ContextProbe, ToolManager, SyscallHandler, InMemoryAuditSink]:
    registry = ToolRegistry()
    tool = _ContextProbe()
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(registry, executor)
    sink = InMemoryAuditSink()
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
            audit_intent_sink=sink,
            require_authenticated_principal=True,
        ),
    )
    return tool, manager, handler, sink


def _request() -> Any:
    return SimpleNamespace(
        action_decision=SimpleNamespace(
            tool="effect_context_probe",
            tool_payload={"target": "record-a"},
        )
    )


def _authorize(
    manager: ToolManager,
    request: Any,
    ctx: _RuntimeContext,
) -> ToolAuthorizationOutcome:
    outcome = manager.authorize(request, ctx)
    assert type(outcome) is ToolAuthorizationOutcome
    assert outcome.authorized is not None
    return outcome


def _execute(
    handler: SyscallHandler,
    request: Any,
    ctx: _RuntimeContext,
    outcome: ToolAuthorizationOutcome,
) -> Any:
    return handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": request,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )


def test_authorized_effect_context_matches_tool_observation() -> None:
    tool, manager, handler, _sink = _rig()
    ctx = _RuntimeContext(_principal())
    handler.begin_run("run-a")
    request = _request()
    outcome = _authorize(manager, request, ctx)

    executed = _execute(handler, request, ctx, outcome)

    assert executed.success is True
    assert outcome.authorized is not None
    assert len(tool.observed) == 1
    observed = tool.observed[0]
    assert observed is outcome.authorized.invocation.effect_context
    assert observed.to_material() == {
        "effect_context_format_version": EFFECT_CONTEXT_FORMAT_VERSION,
        "principal": "alice",
        "tenant": "tenant-a",
        "authentication_source": "oidc",
        "authentication_strength": "hardware-key",
        "service_id": "document-service",
        "session_id_hash": "sha256:session-a",
        "process_id": "process-a",
        "run_id": "run-a",
        "host_binding_commitment": None,
    }


def test_tool_invocation_does_not_retain_pipeline_context() -> None:
    _tool, manager, _handler, _sink = _rig()
    ctx = _RuntimeContext(_principal())
    ctx_ref = weakref.ref(ctx)
    request = _request()

    outcome = _authorize(manager, request, ctx)
    del ctx
    gc.collect()

    assert ctx_ref() is None
    assert outcome.authorized is not None
    invocation = outcome.authorized.invocation
    assert not hasattr(invocation, "context")
    assert not hasattr(invocation.effect_context, "context")


def test_authorized_effect_context_is_frozen_after_authorization() -> None:
    _tool, manager, _handler, _sink = _rig()
    outcome = _authorize(manager, _request(), _RuntimeContext(_principal()))
    assert outcome.authorized is not None

    with pytest.raises(FrozenInstanceError):
        outcome.authorized.invocation.effect_context.principal = "bob"  # type: ignore[misc]


def test_equivalent_but_distinct_effect_context_is_bound_by_value() -> None:
    tool, manager, handler, _sink = _rig()
    authorization_ctx = _RuntimeContext(_principal())
    presentation_ctx = _RuntimeContext(_principal())
    assert authorization_ctx is not presentation_ctx
    assert authorization_ctx.principal is not presentation_ctx.principal
    handler.begin_run("run-a")
    request = _request()
    outcome = _authorize(manager, request, authorization_ctx)

    executed = _execute(handler, request, presentation_ctx, outcome)

    assert executed.success is True
    assert len(tool.observed) == 1
    assert authorization_ctx.extra.get("syscall_intents", []) == []
    assert len(presentation_ctx.extra["syscall_intents"]) == 1


def test_host_binding_mismatch_stops_before_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool, manager, handler, sink = _rig()
    ctx = _RuntimeContext(_principal())
    handler.begin_run("run-a")
    request = _request()
    outcome = _authorize(manager, request, ctx)
    original_builder = syscall_handler_module.build_authorized_effect_context

    def _current_effect_context(
        current_ctx: Any,
        *,
        process_id: str,
        run_id: str | None,
        host_binding_commitment: str | None = None,
    ) -> AuthorizedEffectContext:
        current = original_builder(
            current_ctx,
            process_id=process_id,
            run_id=run_id,
            host_binding_commitment=host_binding_commitment,
        )
        return replace(current, host_binding_commitment="sha256:host-b")

    monkeypatch.setattr(
        syscall_handler_module,
        "build_authorized_effect_context",
        _current_effect_context,
    )

    refused = _execute(handler, request, ctx, outcome)

    assert refused.success is False
    assert refused.error is not None
    assert refused.error.details["reason_code"] == "effect_context_mismatch"
    assert refused.error.details["mismatch_fields"] == "host_binding_commitment"
    assert tool.observed == []
    assert sink.entries == []
    assert ctx.extra.get("syscall_intents", []) == []


def test_intent_commits_authorized_effect_context() -> None:
    _tool, manager, handler, sink = _rig()
    ctx = _RuntimeContext(_principal())
    handler.begin_run("run-a")
    request = _request()
    outcome = _authorize(manager, request, ctx)
    assert outcome.authorized is not None
    sealed = outcome.authorized.invocation.effect_context

    assert _execute(handler, request, ctx, outcome).success is True

    intent = ctx.extra["syscall_intents"][0]
    assert intent["effect_context"] == sealed.to_material()
    assert intent["effect_context_commitment"] == sealed.commitment_sha256
    assert canonical_hash(intent["effect_context"]) == sealed.commitment_sha256
    assert sink.entries[0]["effect_context"] == sealed.to_material()
    assert sink.receipts[0].intent_sha256 == intent["commitment_sha256"]


def test_result_pair_commitment_changes_when_effect_context_changes() -> None:
    def _run(run_id: str) -> tuple[dict[str, Any], dict[str, Any], str | None]:
        _tool, manager, handler, _sink = _rig()
        ctx = _RuntimeContext(_principal(), run_id=run_id)
        handler.begin_run(run_id)
        request = _request()
        outcome = _authorize(manager, request, ctx)
        assert outcome.authorized is not None
        idempotency_key = outcome.authorized.invocation.idempotency_key
        assert _execute(handler, request, ctx, outcome).success is True
        return (
            ctx.extra["syscall_intents"][0],
            ctx.extra["syscall_results"][0],
            idempotency_key,
        )

    first_intent, first_result, first_key = _run("run-a")
    second_intent, second_result, second_key = _run("run-b")

    # Run identity is excluded from durable idempotency by doctrine, so the
    # differing pair proof is specifically carried by the sealed context and
    # its intent commitment rather than by a different logical action key.
    assert first_key == second_key
    assert (
        first_intent["effect_context_commitment"]
        != second_intent["effect_context_commitment"]
    )
    assert first_intent["commitment_sha256"] != second_intent["commitment_sha256"]
    first_pair = syscall_pair_commitments([first_intent], [first_result])
    second_pair = syscall_pair_commitments([second_intent], [second_result])
    assert len(first_pair) == len(second_pair) == 1
    assert first_pair[0] != second_pair[0]
