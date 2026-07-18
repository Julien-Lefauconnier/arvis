# tests/kernel_core/test_result_intent_binding.py
"""Result-to-intent cryptographic binding (a8 section 9, pinned closed).

The a8 audit proved the intent/result correspondence was metadata-only:
no result carried the engagement digest of its intent, so two
same-syscall results could be permuted (together with their causal ids)
without the bijection or the journal digest noticing (9.2, 9.3).

Campaign 6 (Lot 2): the handler stamps each journaled effect result
with the EXACT ``commitment_sha256`` of its intent (single-use, popped
by causal id); the bijection verifies the equality; the journal digest
binds ordered per-pair commitments so a permutation changes the digest
even though causal ids are envelope-stripped from the entry material.

These tests exercise the REAL handler path (not synthetic dicts) plus
the digest-level permutation sensitivity.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.api.commitment import syscall_journal_digest, syscall_pair_commitments
from arvis.kernel_core.syscalls.intent_result_bijection import (
    verify_intent_result_bijection,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _BindTool(BaseTool):
    name = "bind_tool"
    spec = ToolSpec(name="bind_tool", description="binding probe")

    def execute(self, input_data):
        return {"ok": True}


def _rig(monkeypatch):
    registry = ToolRegistry()
    registry.register(_BindTool())
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


def _call(handler, manager, ctx, *, payload):
    decision = SimpleNamespace(tool="bind_tool", tool_payload=payload)
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


def test_result_contains_exact_intent_commitment(monkeypatch):
    handler, manager = _rig(monkeypatch)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    result = _call(handler, manager, ctx, payload={"x": 1})
    assert result.success is True

    intents = ctx.extra["syscall_intents"]
    results = ctx.extra["syscall_results"]
    assert len(intents) == 1 and len(results) == 1
    intent, journaled = intents[0], results[0]

    assert isinstance(intent.get("commitment_sha256"), str)
    assert journaled["intent_commitment_sha256"] == intent["commitment_sha256"]
    assert journaled["syscall_id"] == intent["causal_id"]
    # And the strict bijection accepts the real journals.
    assert verify_intent_result_bijection(intents, results).ok is True


def _two_call_journals(monkeypatch):
    """Two same-syscall calls with distinct payloads, real journals."""
    handler, manager = _rig(monkeypatch)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    assert _call(handler, manager, ctx, payload={"target": "A"}).success is True
    assert _call(handler, manager, ctx, payload={"target": "B"}).success is True
    intents = ctx.extra["syscall_intents"]
    results = ctx.extra["syscall_results"]
    assert len(intents) == 2 and len(results) == 2
    # Distinct payloads engage distinctly.
    assert intents[0]["commitment_sha256"] != intents[1]["commitment_sha256"]
    return intents, results


def _swap_results(results):
    """Audit 9.2 permutation: swap the results together with their ids."""
    swapped = copy.deepcopy(results)
    for key in ("syscall_id", "causal_id"):
        swapped[0][key], swapped[1][key] = swapped[1][key], swapped[0][key]
    return [swapped[1], swapped[0]]


def test_swapped_real_results_are_rejected_by_bijection(monkeypatch):
    intents, results = _two_call_journals(monkeypatch)
    assert verify_intent_result_bijection(intents, results).ok is True

    swapped = _swap_results(results)
    verdict = verify_intent_result_bijection(intents, swapped)
    assert verdict.ok is False
    assert verdict.reason == "intent_commitment_mismatch"


def test_journal_digest_detects_permutation(monkeypatch):
    # Audit 9.3: causal ids are envelope-stripped from the digest
    # material, so pre-fix a permutation left the journal digest
    # unchanged. The ordered pair commitments now bind the pairing.
    intents, results = _two_call_journals(monkeypatch)
    honest = syscall_journal_digest(intents, results)
    swapped = syscall_journal_digest(intents, _swap_results(results))
    assert honest != swapped


def test_pair_commitments_are_ordered_and_pair_sensitive(monkeypatch):
    intents, results = _two_call_journals(monkeypatch)
    pairs = syscall_pair_commitments(intents, results)
    assert len(pairs) == 2
    assert pairs[0] != pairs[1]
    swapped_pairs = syscall_pair_commitments(intents, _swap_results(results))
    assert pairs != swapped_pairs
