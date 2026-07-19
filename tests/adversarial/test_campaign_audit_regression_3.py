"""Campaign 7 red tests: reproduce remaining effect-path integrity gaps.

These tests describe the target secure behaviour. Findings whose lot is
still pending are strict xfails: an unexpected pass fails the gate until
the marker is deliberately removed with the corresponding fix.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.access.models import AuthenticatedPrincipal
from arvis.kernel_core.syscalls.audit_sink import AuditReceipt, InMemoryAuditSink
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.authorized_invocation import (
    AuthorizedInvocation,
    UnauthorizedExecutionError,
)
from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolAuthorizationOutcome, ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _RecordingTool(BaseTool):
    def __init__(self, name: str, *, requires_confirmation: bool = False) -> None:
        self.name = name
        self.spec = ToolSpec(
            name=name,
            description="campaign 7 probe",
            requires_confirmation=requires_confirmation,
        )
        self.payloads: list[dict[str, Any]] = []

    def execute(self, input_data: dict[str, Any]) -> Any:
        payload = input_data.get("tool_payload", {})
        self.payloads.append(dict(payload))
        return {"ok": True, "tool": self.name}


def _result(tool_name: str, payload: dict[str, Any]) -> Any:
    return SimpleNamespace(
        action_decision=SimpleNamespace(tool=tool_name, tool_payload=payload)
    )


def _ctx(
    *,
    user_id: str = "u1",
    confirmation_id: str | None = None,
    authenticated: bool = False,
) -> Any:
    carrier = (
        SimpleNamespace(confirmation_id=confirmation_id)
        if confirmation_id is not None
        else None
    )
    ctx = SimpleNamespace(
        extra={},
        user_id=user_id,
        confirmation_result=carrier,
    )
    if authenticated:
        ctx.principal = AuthenticatedPrincipal(
            user_id=user_id,
            authentication_source="test",
            authentication_strength="strong",
        )
    return ctx


def _rig(
    *tools: _RecordingTool,
    sink: Any | None = None,
    require_sink: bool = False,
    confirmation_registry: ConfirmationRegistry | None = None,
) -> tuple[SyscallHandler, ToolManager, ToolExecutor]:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(
        registry=registry,
        executor=executor,
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
            require_authenticated_principal=require_sink,
        ),
    )
    return handler, manager, executor


def _activate_outcome(
    manager: ToolManager,
    outcome: ToolAuthorizationOutcome,
    *,
    intent_sha256: str = "a" * 64,
) -> None:
    assert outcome.authorized is not None
    receipt = AuditReceipt(
        receipt_id=f"receipt:{outcome.authorized.nonce}",
        run_id=None,
        causal_id=f"causal:{outcome.authorized.nonce}",
        intent_sha256=intent_sha256,
        durable_position="1",
        store_fingerprint="db:test",
        committed_at="2026-07-19T00:00:00+00:00",
    )
    assert manager.activate_authorized(
        outcome.authorized,
        receipt=receipt,
        intent_sha256=intent_sha256,
        run_id=None,
        causal_id=f"causal:{outcome.authorized.nonce}",
    )


def test_legitimate_capability_cannot_mint_fresh_nonce() -> None:
    safe = _RecordingTool("safe")
    danger = _RecordingTool("danger")
    _handler, manager, _executor = _rig(safe, danger)
    ctx = _ctx()

    safe_outcome = manager.authorize(_result("safe", {"target": "A"}), ctx)
    assert isinstance(safe_outcome, ToolAuthorizationOutcome)
    assert safe_outcome.authorized is not None

    legitimate = safe_outcome.authorized
    assert not hasattr(legitimate, "_authority_token")
    forged = AuthorizedInvocation(
        invocation=ToolInvocation(
            tool_name="danger",
            payload={"target": "B"},
            process_id="p1",
            user_id="u1",
            context=ctx,
        ),
        authorization_snapshot=legitimate.authorization_snapshot,
        nonce="attacker-selected-fresh-nonce",
    )

    with pytest.raises(UnauthorizedExecutionError):
        manager.execute_authorized(forged, _result("safe", {}), ctx)
    assert danger.payloads == []


def test_payload_mutation_after_authorization_does_not_change_effect() -> None:
    tool = _RecordingTool("mutate")
    _handler, manager, _executor = _rig(tool)
    ctx = _ctx()
    payload = {"target": "A", "nested": {"value": 1}}

    outcome = manager.authorize(_result("mutate", payload), ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None

    payload["target"] = "B"
    payload["nested"]["value"] = 2
    _activate_outcome(manager, outcome)
    manager.execute_authorized(outcome.authorized, _result("mutate", payload), ctx)

    assert tool.payloads == [{"target": "A", "nested": {"value": 1}}]


def test_handler_refuses_arbitrary_authorization_wrapper(monkeypatch) -> None:
    tool = _RecordingTool("wrapped")
    handler, manager, _executor = _rig(tool)
    ctx = _ctx()
    pipeline_result = _result("wrapped", {"x": 1})
    outcome = manager.authorize(pipeline_result, ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None

    captured: list[dict[str, Any] | None] = []
    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    real_digest = handler_module.effect_engagement_digest

    def _capture(**kwargs: Any) -> str:
        captured.append(kwargs.get("authorization_snapshot"))
        return real_digest(**kwargs)

    monkeypatch.setattr(handler_module, "effect_engagement_digest", _capture)
    forged_wrapper = SimpleNamespace(
        authorized=outcome.authorized,
        refusal=None,
        snapshot_material={
            "authorization_version": 1,
            "tool_name": "wrapped",
            "allowed": True,
            "reason": "forged",
            "principal": "attacker",
            "tenant": "forged-tenant",
            "risk_bucket": 0.0,
            "confirmed": False,
            "confirmation_commitment": None,
        },
    )

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": forged_wrapper,
            },
        )
    )

    assert result.success is False
    assert tool.payloads == []
    assert captured == []


def test_sink_failure_revokes_capability_and_prevents_direct_execution() -> None:
    class _InvalidSink:
        def append(self, intent: dict[str, Any]) -> AuditReceipt:
            return AuditReceipt(
                receipt_id="r1",
                run_id=intent.get("run_id"),
                causal_id=str(intent.get("causal_id", "")),
                intent_sha256="wrong-intent",
                durable_position="1",
                store_fingerprint="db:test",
                committed_at="2026-07-18T00:00:00+00:00",
            )

    tool = _RecordingTool("sink_fail")
    handler, manager, _executor = _rig(tool, sink=_InvalidSink(), require_sink=True)
    ctx = _ctx()
    pipeline_result = _result("sink_fail", {"x": 1})
    outcome = manager.authorize(pipeline_result, ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None

    refused = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )
    assert refused.success is False

    with pytest.raises(UnauthorizedExecutionError):
        manager.execute_authorized(outcome.authorized, pipeline_result, ctx)
    assert tool.payloads == []


def test_policy_exception_releases_reserved_confirmation(monkeypatch) -> None:
    confirmations = ConfirmationRegistry()
    tool = _RecordingTool("confirm", requires_confirmation=True)
    _handler, manager, _executor = _rig(tool, confirmation_registry=confirmations)
    payload = {"x": 1}
    record = confirmations.issue(
        tool_name="confirm",
        payload=payload,
        principal="u1",
        tenant=None,
    )
    ctx = _ctx(confirmation_id=record.confirmation_id)

    def _boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("policy exploded")

    monkeypatch.setattr(ToolPolicyEvaluator, "evaluate", staticmethod(_boom))

    with pytest.raises(RuntimeError, match="policy exploded"):
        manager.authorize(_result("confirm", payload), ctx)

    # The record must be reservable again after any pre-effect exception.
    reserved_again = confirmations.reserve(
        confirmation_id=record.confirmation_id,
        tool_name="confirm",
        payload=payload,
        principal="u1",
        tenant=None,
    )
    assert reserved_again is not None


def test_two_runs_with_same_prefix_have_distinct_causal_ids() -> None:
    handler = SyscallHandler(runtime_state=None, scheduler=None)
    syscall = Syscall(name="tool.execute", args={"process_id": "p1"})

    handler.begin_run("0123456789abAAAAAAAAAAAAAAAAAAAA")
    first = handler._build_syscall_id(syscall, tick=1, seq=1)
    handler.begin_run("0123456789abBBBBBBBBBBBBBBBBBBBB")
    second = handler._build_syscall_id(syscall, tick=1, seq=1)

    assert first != second


def test_production_effect_refuses_unstamped_principal() -> None:
    tool = _RecordingTool("identity")
    sink = InMemoryAuditSink()
    handler, manager, _executor = _rig(tool, sink=sink, require_sink=True)
    ctx = _ctx(user_id="declared-only-user")
    pipeline_result = _result("identity", {"x": 1})
    outcome = manager.authorize(pipeline_result, ctx)

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )

    assert result.success is False
    assert tool.payloads == []


def test_in_memory_sink_is_refused_when_durability_is_required() -> None:
    tool = _RecordingTool("memory_sink")
    sink = InMemoryAuditSink()
    handler, manager, _executor = _rig(tool, sink=sink, require_sink=True)
    ctx = _ctx(authenticated=True)
    pipeline_result = _result("memory_sink", {"x": 1})
    outcome = manager.authorize(pipeline_result, ctx)

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )

    assert result.success is False
    assert tool.payloads == []
