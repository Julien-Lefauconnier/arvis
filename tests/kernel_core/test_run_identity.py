# tests/kernel_core/test_run_identity.py
"""Global run identity (a8 section 17, pinned closed, campaign 6 Lot 5).

The a8 audit proved causal ids were built from local elements only
(syscall, process, tick, counter): two runs, each on a fresh instance,
produced IDENTICAL causal ids, so a shared sink could not reconcile
them (collision, ambiguity after a crash, wrong multi-worker
aggregation).

Campaign 6: a fresh unguessable ``run_id`` is generated at run entry
(``SyscallHandler.begin_run``, called by the runtime), prefixes every
causal id and is journaled on every intent and result. It is ENVELOPE
identity: like the causal ids it prefixes, it is stripped from the
hashed material, so the deterministic-commitment contract of the
kernel ("what the run did", not "which run did it") is preserved; the
run <-> commitment anchoring is the durable sink's job (receipt).
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.api.commitment import syscall_journal_digest
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _RunTool(BaseTool):
    name = "run_tool"
    spec = ToolSpec(name="run_tool", description="run identity probe")

    def execute(self, input_data):
        return {"ok": True}


def _rig(monkeypatch):
    registry = ToolRegistry()
    registry.register(_RunTool())
    executor = ToolExecutor(registry)
    manager = ToolManager(registry=registry, executor=executor)
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
        ),
    )
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        staticmethod(
            lambda invocation, reg, **kwargs: SimpleNamespace(allowed=True, reason=None)
        ),
    )
    return handler, manager


def _call(handler, manager, ctx):
    decision = SimpleNamespace(tool="run_tool", tool_payload={"x": 1})
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


def test_causal_ids_collide_between_runs_without_run_identity(monkeypatch):
    # The exact a8 scenario: two fresh instances, no run identity, same
    # call: the local elements (tick 0, counter 1) coincide and so do
    # the causal ids. Pinned as the motivation for the fix.
    ids = []
    for _ in range(2):
        handler, manager = _rig(monkeypatch)
        ctx = SimpleNamespace(extra={}, user_id="u1")
        assert _call(handler, manager, ctx).success is True
        ids.append(ctx.extra["syscall_intents"][0]["causal_id"])
    assert ids[0] == ids[1]


def test_causal_ids_are_unique_between_runs(monkeypatch):
    ids = []
    run_ids = []
    for _ in range(2):
        handler, manager = _rig(monkeypatch)
        run_id = uuid.uuid4().hex
        handler.begin_run(run_id)
        ctx = SimpleNamespace(extra={}, user_id="u1")
        assert _call(handler, manager, ctx).success is True
        ids.append(ctx.extra["syscall_intents"][0]["causal_id"])
        run_ids.append(run_id)
    assert run_ids[0] != run_ids[1]
    assert ids[0] != ids[1]


def test_intent_and_result_carry_the_run_id(monkeypatch):
    handler, manager = _rig(monkeypatch)
    run_id = uuid.uuid4().hex
    handler.begin_run(run_id)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    assert _call(handler, manager, ctx).success is True

    intent = ctx.extra["syscall_intents"][0]
    journaled = ctx.extra["syscall_results"][0]
    assert intent["run_id"] == run_id
    assert journaled["run_id"] == run_id
    assert intent["causal_id"].startswith(f"syscall:{run_id[:12]}:")
    assert journaled["syscall_id"] == intent["causal_id"]


def test_run_identity_is_envelope_only(monkeypatch):
    # Deterministic-commitment contract preserved: the same call under
    # two DIFFERENT run identities yields the same engagement digest
    # and the same journal digest. The run identity lives on the
    # journaled entries (for the sink), never in the hashed material.
    journals = []
    commitments = []
    for _ in range(2):
        handler, manager = _rig(monkeypatch)
        handler.begin_run(uuid.uuid4().hex)
        ctx = SimpleNamespace(extra={}, user_id="u1")
        assert _call(handler, manager, ctx).success is True
        intents = ctx.extra["syscall_intents"]
        results = ctx.extra["syscall_results"]
        commitments.append(intents[0]["commitment_sha256"])
        journals.append(syscall_journal_digest(intents, results))
    assert commitments[0] == commitments[1]
    assert journals[0] == journals[1]


def test_begin_run_resets_pairing_state(monkeypatch):
    # A run boundary never leaks intent pairing into the next run: two
    # begin_run cycles on one handler journal consistently.
    handler, manager = _rig(monkeypatch)
    for _ in range(2):
        handler.begin_run(uuid.uuid4().hex)
        ctx = SimpleNamespace(extra={}, user_id="u1")
        assert _call(handler, manager, ctx).success is True
        intent = ctx.extra["syscall_intents"][0]
        journaled = ctx.extra["syscall_results"][0]
        assert journaled["intent_commitment_sha256"] == intent["commitment_sha256"]
