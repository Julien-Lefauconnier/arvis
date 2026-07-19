# tests/adversarial/test_audit_regression_2.py
"""Campaign 6 audit-remediation smoke: one attack vector per closed finding.

This is the security regression guard for the 0.1.0a8 external audit.
Each test reproduces the ATTACK the audit described and asserts it now
fails. If any future change reopens a finding, exactly one of these
turns red. Kept together, and phrased as attacks, so the guarantee is
legible: these are the things an adversary could do against a8 and can
no longer do.

Findings covered (a8 report sections):
- 7: lossy canonicalization collisions (bytes/bytearray, path types,
  homonymous classes, dropped private state)
- 8: intent recorded before the authorization existed; stale snapshot
  reusable through the mutable ctx.extra channel
- 9: result not bound to its intent; same-syscall permutation invisible
  to the bijection and to the journal digest
- 10: publicly mintable authority; reusable capability
- 11: confirmation consumed on a pre-effect schema refusal
- 12: two human decisions on the same effect indistinguishable
- 14: declarative durability (``lambda intent: None`` as a sink)
- 17: causal ids colliding between runs
"""

from __future__ import annotations

import copy
import uuid
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import pytest

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.api.commitment import syscall_journal_digest
from arvis.kernel_core.canonicalization import (
    NonCanonicalizableError,
    canonical_hash,
)
from arvis.kernel_core.syscalls.audit_sink import (
    AuditReceipt,
    AuditSinkDurabilityClass,
    AuditSinkManifest,
    InMemoryAuditSink,
)
from arvis.kernel_core.syscalls.intent_result_bijection import (
    verify_intent_result_bijection,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.authorized_invocation import UnauthorizedExecutionError
from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec
from arvis.tools.tool_result import PRE_EFFECT_REFUSAL
from tests.support.tool_execution import execute_authorized_for_tests


class _Tool(BaseTool):
    name = "c6_tool"
    spec = ToolSpec(name="c6_tool", description="campaign 6 smoke probe")

    def __init__(self) -> None:
        self.executed: list[dict] = []

    def execute(self, input_data):
        self.executed.append(input_data)
        return {"ok": True}


class _DatabaseSink(InMemoryAuditSink):
    def __init__(self) -> None:
        super().__init__()
        self.manifest = AuditSinkManifest(
            sink_kind="test_database",
            durability_class=AuditSinkDurabilityClass.DATABASE,
            transactional=True,
            append_only=True,
            store_fingerprint=self._store_fingerprint,
            implementation_version="1",
        )


def _rig(monkeypatch, *, sink=None, require_sink=False, verdicts=None):
    registry = ToolRegistry()
    tool = _Tool()
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
    scripted = list(verdicts) if verdicts else None

    def _evaluate(invocation, reg, **kwargs):
        if scripted:
            allowed, reason = scripted.pop(0)
            return SimpleNamespace(allowed=allowed, reason=reason)
        return SimpleNamespace(allowed=True, reason=None)

    monkeypatch.setattr(ToolPolicyEvaluator, "evaluate", staticmethod(_evaluate))
    return handler, manager, executor, tool


def _call(handler, manager, ctx, *, payload=None):
    decision = SimpleNamespace(tool="c6_tool", tool_payload=payload or {"x": 1})
    pipeline_result = SimpleNamespace(action_decision=decision)
    authorization = manager.authorize(pipeline_result, ctx)
    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": authorization,
            },
        )
    )
    return result, authorization


# -----------------------------------------------------------------
# Section 7: the canonicalization collisions
# -----------------------------------------------------------------


def test_a8_canonicalization_collisions_are_closed():
    # bytes vs bytearray, concrete path types, homonymous classes and
    # hidden private state each produced identical digests under a8.
    assert canonical_hash(b"A") != canonical_hash(bytearray(b"A"))
    assert canonical_hash(Path("/tmp/a")) != canonical_hash(PurePosixPath("/tmp/a"))

    def make_record(module: str) -> type:
        cls = type("Record", (), {})
        cls.__module__ = module
        cls.__qualname__ = "Record"
        return cls

    a = make_record("module_a")()
    a.value = 1
    b = make_record("module_b")()
    b.value = 1
    assert canonical_hash(a) != canonical_hash(b)

    class Cmd:
        def __init__(self) -> None:
            self.target = "A"
            self._secret = 1

    with pytest.raises(NonCanonicalizableError):
        canonical_hash(Cmd())


# -----------------------------------------------------------------
# Section 8: authorization before intent, no stale snapshot
# -----------------------------------------------------------------


def test_a8_intent_binds_this_calls_verdict_not_a_stale_one(monkeypatch):
    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    captured: list[dict] = []
    real_digest = handler_module.effect_engagement_digest

    def _capture(**kwargs):
        captured.append(dict(kwargs))
        return real_digest(**kwargs)

    monkeypatch.setattr(handler_module, "effect_engagement_digest", _capture)

    handler, manager, _executor, tool = _rig(
        monkeypatch, verdicts=[(True, "allowed"), (False, "risk_above_max")]
    )
    ctx = SimpleNamespace(extra={}, user_id="u1")
    first, _ = _call(handler, manager, ctx)
    assert first.success is True
    # First call: the snapshot exists BEFORE the intent (a8 ran with
    # None here) and is the allowed verdict.
    assert captured[0]["authorization_snapshot"]["allowed"] is True

    second, _authorization = _call(handler, manager, ctx)
    assert second.success is False
    # Second, denied call: its intent binds ITS OWN denial, never the
    # first call's allowed snapshot left on a mutable channel.
    assert captured[1]["authorization_snapshot"]["allowed"] is False
    assert captured[1]["authorization_snapshot"]["reason"] == "risk_above_max"
    assert len(tool.executed) == 1


def test_a8_bare_tool_execute_without_authorization_is_refused(monkeypatch):
    handler, _manager, _executor, tool = _rig(monkeypatch)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    decision = SimpleNamespace(tool="c6_tool", tool_payload={})
    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": SimpleNamespace(action_decision=decision),
                "ctx": ctx,
            },
        )
    )
    assert result.success is False
    assert tool.executed == []


# -----------------------------------------------------------------
# Section 9: result bound to its exact intent
# -----------------------------------------------------------------


def test_a8_same_syscall_permutation_is_refused_everywhere(monkeypatch):
    handler, manager, _executor, _tool = _rig(monkeypatch)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    assert _call(handler, manager, ctx, payload={"target": "A"})[0].success
    assert _call(handler, manager, ctx, payload={"target": "B"})[0].success
    intents = ctx.extra["syscall_intents"]
    results = ctx.extra["syscall_results"]
    assert verify_intent_result_bijection(intents, results).ok is True

    swapped = copy.deepcopy(results)
    for key in ("syscall_id", "causal_id"):
        swapped[0][key], swapped[1][key] = swapped[1][key], swapped[0][key]
    swapped = [swapped[1], swapped[0]]

    # The a8 permutation passed the bijection AND left the journal
    # digest unchanged. Both now refuse it.
    verdict = verify_intent_result_bijection(intents, swapped)
    assert verdict.ok is False
    assert verdict.reason == "intent_commitment_mismatch"
    assert syscall_journal_digest(intents, results) != syscall_journal_digest(
        intents, swapped
    )


# -----------------------------------------------------------------
# Section 10: private, single-use capability
# -----------------------------------------------------------------


def test_a8_authority_is_not_mintable_and_capability_is_single_use(monkeypatch):
    handler, manager, executor, tool = _rig(monkeypatch)
    # The a8 bypass: executor.authority.authorize(...) by any holder.
    assert not hasattr(executor, "authority")
    # The single claim is already held by the manager.
    with pytest.raises(UnauthorizedExecutionError):
        executor._claim_minting_authority()

    # Replay of a legitimately minted capability: first presentation
    # runs, the second is refused.
    ctx = SimpleNamespace(extra={}, user_id="u1")
    decision = SimpleNamespace(tool="c6_tool", tool_payload={"x": 1})
    pipeline_result = SimpleNamespace(action_decision=decision)
    outcome = manager.authorize(pipeline_result, ctx)
    assert outcome is not None and outcome.authorized is not None
    first = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )
    assert first.success is True
    with pytest.raises(UnauthorizedExecutionError):
        execute_authorized_for_tests(manager, outcome.authorized, pipeline_result, ctx)
    assert len(tool.executed) == 1


# -----------------------------------------------------------------
# Section 11: confirmation never burned before the effect
# -----------------------------------------------------------------


def test_a8_schema_refusal_never_consumes_the_confirmation():
    class _StrictTool(BaseTool):
        name = "strict"
        spec = ToolSpec(
            name="strict",
            description="",
            input_schema={
                "type": "object",
                "properties": {"n": {"type": "integer"}},
                "required": ["n"],
            },
        )

        def execute(self, input_data):
            raise AssertionError("the effect must never run")

    registry = ToolRegistry()
    registry.register(_StrictTool())
    executor = ToolExecutor(registry)
    confirmations = ConfirmationRegistry()
    manager = ToolManager(
        registry=registry,
        executor=executor,
        confirmation_registry=confirmations,
    )
    payload = {"n": "not-an-integer"}
    conf = confirmations.issue(tool_name="strict", payload=payload, principal="u1")
    ctx = SimpleNamespace(
        extra={},
        user_id="u1",
        confirmation_result=SimpleNamespace(confirmation_id=conf.confirmation_id),
    )
    outcome = manager.authorize(
        SimpleNamespace(
            action_decision=SimpleNamespace(tool="strict", tool_payload=payload)
        ),
        ctx,
    )
    assert outcome is not None and outcome.refusal is not None
    assert outcome.refusal.effect_boundary == PRE_EFFECT_REFUSAL
    # The a8 attack burned the confirmation here; it stays pending.
    assert confirmations.pending_count() == 1


# -----------------------------------------------------------------
# Section 12: one human decision, one commitment
# -----------------------------------------------------------------


def test_a8_two_decisions_on_the_same_effect_commit_differently():
    registry = ConfirmationRegistry()
    a = registry.issue(tool_name="t", payload={"cmd": "go"}, principal="u1")
    b = registry.issue(tool_name="t", payload={"cmd": "go"}, principal="u1")
    assert a.payload_sha256 == b.payload_sha256
    assert a.record_commitment != b.record_commitment


# -----------------------------------------------------------------
# Section 14: durability proven, not declared
# -----------------------------------------------------------------


def test_a8_declarative_sink_no_longer_satisfies_production(monkeypatch):
    # The audit's verbatim bypass: lambda intent: None.
    handler, manager, _executor, tool = _rig(
        monkeypatch, sink=lambda intent: None, require_sink=True
    )
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result, _ = _call(handler, manager, ctx)
    assert result.success is False
    assert tool.executed == []


def test_a8_lying_sink_receipt_refuses_the_effect(monkeypatch):
    class _LyingSink:
        def append(self, intent):
            return AuditReceipt(
                receipt_id="r1",
                run_id=intent.get("run_id"),
                causal_id=str(intent.get("causal_id", "")),
                intent_sha256="wrong",
                durable_position="0",
                store_fingerprint="memory:lying",
                committed_at="2026-07-18T00:00:00+00:00",
            )

    handler, manager, _executor, tool = _rig(
        monkeypatch, sink=_LyingSink(), require_sink=True
    )
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result, _ = _call(handler, manager, ctx)
    assert result.success is False
    assert tool.executed == []


# -----------------------------------------------------------------
# Section 17: run identity
# -----------------------------------------------------------------


def test_a8_causal_ids_no_longer_collide_between_runs(monkeypatch):
    ids = []
    for _ in range(2):
        handler, manager, _executor, _tool = _rig(monkeypatch)
        handler.begin_run(uuid.uuid4().hex)
        ctx = SimpleNamespace(extra={}, user_id="u1")
        assert _call(handler, manager, ctx)[0].success is True
        ids.append(ctx.extra["syscall_intents"][0]["causal_id"])
    assert ids[0] != ids[1]


def test_a8_end_to_end_honest_run_still_proves(monkeypatch):
    # The positive control: with every defense active (durable sink,
    # run identity, sealed authorization), an honest run proves cleanly
    # end to end: valid receipt, strict bijection, run-stable digest.
    sink = _DatabaseSink()
    handler, manager, _executor, tool = _rig(monkeypatch, sink=sink, require_sink=True)
    handler.begin_run(uuid.uuid4().hex)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result, _ = _call(handler, manager, ctx)
    assert result.success is True
    assert len(tool.executed) == 1
    intents = ctx.extra["syscall_intents"]
    results = ctx.extra["syscall_results"]
    assert verify_intent_result_bijection(intents, results).ok is True
    assert sink.receipts[0].intent_sha256 == intents[0]["commitment_sha256"]
    assert "audit_receipt" in intents[0]
