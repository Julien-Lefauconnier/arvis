"""Explicit test compositions for focused tool lifecycle tests.

These helpers intentionally live outside :mod:`arvis`. They may exercise
private lifecycle primitives in unit tests, but are excluded from wheels by
the package configuration and cannot become a production effect route.
"""

from __future__ import annotations

from typing import Any

from arvis.kernel_core.syscalls.audit_sink import AuditReceipt, InMemoryAuditSink
from arvis.kernel_core.syscalls.engagement import stable_hash
from arvis.tools.authorized_invocation import AuthorizedInvocation
from arvis.tools.manager import ToolManager
from arvis.tools.tool_result import ToolResult


def activate_authorized_for_tests(
    manager: ToolManager,
    authorized: Any,
    *,
    receipt: Any,
    intent_sha256: str,
    run_id: str | None,
    causal_id: str,
) -> bool:
    return manager._activate_authorized(
        authorized,
        receipt=receipt,
        intent_sha256=intent_sha256,
        run_id=run_id,
        causal_id=causal_id,
    )


def abort_authorized_for_tests(manager: ToolManager, authorized: Any) -> bool:
    return manager._abort_authorized(authorized)


def execute_authorized_for_tests(
    manager: ToolManager,
    authorized: Any,
    result: Any,
    ctx: Any,
) -> ToolResult | None:
    return manager._execute_authorized(authorized, result, ctx)


def run_tool_for_tests(
    manager: ToolManager,
    result: Any,
    ctx: Any,
) -> ToolResult | None:
    """Authorize, locally acknowledge and execute one tool in a unit test."""
    outcome = manager.authorize(result, ctx)
    if outcome is None:
        return None
    if outcome.refusal is not None:
        return outcome.refusal
    authorized = outcome.authorized
    if type(authorized) is not AuthorizedInvocation:
        raise RuntimeError("authorized test outcome has no exact capability")

    causal_id = f"tool-manager-test-run:{authorized.nonce}"
    intent_sha256 = stable_hash(
        {
            "local_tool_run_version": 2,
            "causal_id": causal_id,
            "tool": authorized.invocation.tool_name,
            "payload_sha256": authorized.payload_sha256,
            "idempotency_key": authorized.invocation.idempotency_key,
            "effect_context": authorized.invocation.effect_context.to_material(),
            "authorization_snapshot": dict(authorized.authorization_snapshot),
        }
    )
    local_intent = {
        "kind": "syscall_intent",
        "syscall": "tool.execute",
        "causal_id": causal_id,
        "process_id": authorized.invocation.process_id or "none",
        "idempotency_key": authorized.invocation.idempotency_key,
        "effect_context": authorized.invocation.effect_context.to_material(),
        "effect_context_commitment": (
            authorized.invocation.effect_context.commitment_sha256
        ),
        "commitment_sha256": intent_sha256,
    }
    try:
        receipt: AuditReceipt = InMemoryAuditSink().append(local_intent)
        if not activate_authorized_for_tests(
            manager,
            authorized,
            receipt=receipt,
            intent_sha256=intent_sha256,
            run_id=None,
            causal_id=causal_id,
        ):
            raise RuntimeError("the test-only outbox could not activate capability")
        return execute_authorized_for_tests(manager, authorized, result, ctx)
    except Exception:
        abort_authorized_for_tests(manager, authorized)
        raise


__all__ = [
    "abort_authorized_for_tests",
    "activate_authorized_for_tests",
    "execute_authorized_for_tests",
    "run_tool_for_tests",
]
