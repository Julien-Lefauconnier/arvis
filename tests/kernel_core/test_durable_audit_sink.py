# tests/kernel_core/test_durable_audit_sink.py
"""Durable audit sink protocol (a8 section 14, pinned closed, Lot 6).

The a8 audit proved the durability of the intent outbox was
declarative: ``audit_intent_sink=lambda intent: None`` satisfied every
control. The sink now ANSWERS: it returns an :class:`AuditReceipt`
binding exactly the persisted intent (engagement digest, run identity)
and where it durably lives (position, store fingerprint). The syscall
boundary validates every receipt fail-closed; the receipt is journaled
on the intent entry as ENVELOPE material (stripped from the hashed
digest, like the run identity), so the deterministic-commitment
contract holds while the sink anchors run <-> proof durably.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.api.commitment import syscall_journal_digest
from arvis.kernel_core.syscalls.audit_sink import (
    AuditReceipt,
    DurableAuditSink,
    InMemoryAuditSink,
    validate_receipt,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _SinkTool(BaseTool):
    name = "sink_tool"
    spec = ToolSpec(name="sink_tool", description="sink probe")

    def __init__(self) -> None:
        self.executed: list[dict] = []

    def execute(self, input_data):
        self.executed.append(input_data)
        return {"ok": True}


def _rig(monkeypatch, *, sink, require_sink=False):
    registry = ToolRegistry()
    tool = _SinkTool()
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(registry=registry, executor=executor)
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
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        staticmethod(
            lambda invocation, reg, **kwargs: SimpleNamespace(allowed=True, reason=None)
        ),
    )
    return handler, manager, tool


def _call(handler, manager, ctx):
    decision = SimpleNamespace(tool="sink_tool", tool_payload={"x": 1})
    pipeline_result = SimpleNamespace(action_decision=decision)
    authorization = manager.authorize(pipeline_result, ctx)
    return handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": authorization,
            },
        )
    )


def test_durable_sink_returns_valid_receipt(monkeypatch):
    sink = InMemoryAuditSink()
    assert isinstance(sink, DurableAuditSink)
    handler, manager, tool = _rig(monkeypatch, sink=sink, require_sink=True)
    run_id = uuid.uuid4().hex
    handler.begin_run(run_id)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result = _call(handler, manager, ctx)
    assert result.success is True
    assert tool.executed

    intent = ctx.extra["syscall_intents"][0]
    receipt = sink.receipts[0]
    assert validate_receipt(receipt, intent) is None
    assert receipt.intent_sha256 == intent["commitment_sha256"]
    assert receipt.run_id == run_id
    # Journaled on the intent entry, envelope material.
    assert intent["audit_receipt"]["receipt_id"] == receipt.receipt_id
    assert intent["audit_receipt"]["durable_position"] == receipt.durable_position


def test_invalid_receipt_refuses_the_effect(monkeypatch):
    class _LyingSink:
        def append(self, intent):
            return AuditReceipt(
                receipt_id="r1",
                run_id=intent.get("run_id"),
                causal_id=str(intent.get("causal_id", "")),
                intent_sha256="not-the-engagement-digest",
                durable_position="0",
                store_fingerprint="memory:lying",
                committed_at="2026-07-18T00:00:00+00:00",
            )

    handler, manager, tool = _rig(monkeypatch, sink=_LyingSink(), require_sink=True)
    handler.begin_run(uuid.uuid4().hex)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result = _call(handler, manager, ctx)
    assert result.success is False
    assert result.error is not None
    assert tool.executed == []  # the effect never ran


def test_receipt_for_a_different_run_is_refused(monkeypatch):
    class _WrongRunSink:
        def append(self, intent):
            return AuditReceipt(
                receipt_id="r1",
                run_id="another-run-entirely",
                causal_id=str(intent.get("causal_id", "")),
                intent_sha256=str(intent.get("commitment_sha256", "")),
                durable_position="0",
                store_fingerprint="memory:wrong-run",
                committed_at="2026-07-18T00:00:00+00:00",
            )

    handler, manager, tool = _rig(monkeypatch, sink=_WrongRunSink(), require_sink=True)
    handler.begin_run(uuid.uuid4().hex)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result = _call(handler, manager, ctx)
    assert result.success is False
    assert tool.executed == []


def test_raising_sink_refuses_the_effect(monkeypatch):
    class _CrashingSink:
        def append(self, intent):
            raise RuntimeError("store unavailable")

    handler, manager, tool = _rig(monkeypatch, sink=_CrashingSink(), require_sink=True)
    handler.begin_run(uuid.uuid4().hex)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result = _call(handler, manager, ctx)
    assert result.success is False
    assert tool.executed == []


def test_receipt_is_envelope_material(monkeypatch):
    # Deterministic-commitment contract: the same call with and without
    # a durable sink, and across two runs with distinct receipts,
    # yields the SAME journal digest. The receipt anchors, the digest
    # binds; they never mix.
    digests = []
    for sink in (None, InMemoryAuditSink(), InMemoryAuditSink()):
        handler, manager, _tool = _rig(monkeypatch, sink=sink)
        handler.begin_run(uuid.uuid4().hex)
        ctx = SimpleNamespace(extra={}, user_id="u1")
        assert _call(handler, manager, ctx).success is True
        digests.append(
            syscall_journal_digest(
                ctx.extra["syscall_intents"], ctx.extra["syscall_results"]
            )
        )
    assert digests[0] == digests[1] == digests[2]
