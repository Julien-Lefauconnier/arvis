# tests/adversarial/test_audit_regression.py
"""Campaign 5 audit-remediation smoke: one attack vector per closed finding.

This is the security regression guard for the 0.1.0a7 external audit.
Each test reproduces the ATTACK the audit described and asserts it now
fails. If any future change reopens a finding, exactly one of these
turns red. Kept together, and phrased as attacks, so the guarantee is
legible: these are the things an adversary could do against a7 and can
no longer do.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from arvis import CognitiveOS
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.kernel_core.canonicalization import canonical_hash
from arvis.kernel_core.syscalls.intent_result_bijection import (
    verify_intent_result_bijection,
)
from arvis.tools.authorized_invocation import (
    InvocationAuthority,
    UnauthorizedExecutionError,
)
from arvis.tools.confirmation import ConfirmationRegistry, payload_commitment
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry

# ---------------------------------------------------------------
# P0: payload collision -> confirmation transfer
# ---------------------------------------------------------------


def test_attack_confirmation_for_one_record_cannot_authorize_another():
    # a7: deleting record-A and record-B produced the same payload
    # commitment, so a confirmation for A consumed for B.
    reg = ConfirmationRegistry()
    conf = reg.issue(
        tool_name="delete", payload={"id": "record-A", "op": "delete"}, principal="u1"
    )
    stolen = reg.reserve(
        confirmation_id=conf.confirmation_id,
        tool_name="delete",
        payload={"id": "record-B", "op": "delete"},
        principal="u1",
    )
    assert stolen is None


def test_attack_business_fields_cannot_be_collided_away():
    # a7 stripped id / timestamp / process_id from business payloads
    # and collapsed bytes and key types before hashing.
    assert payload_commitment({"id": "A"}) != payload_commitment({"id": "B"})
    assert canonical_hash({"blob": b"A"}) != canonical_hash({"blob": b"B"})
    assert canonical_hash({1: "x"}) != canonical_hash({"1": "x"})


# ---------------------------------------------------------------
# P1-5: a policy denial after confirmation burned the confirmation
# ---------------------------------------------------------------


def test_attack_policy_denial_does_not_burn_a_confirmation():
    reg = ConfirmationRegistry()
    conf = reg.issue(tool_name="t", payload={"id": "A"}, principal="u1")
    # A reservation that is released (as the manager does on a pre-effect
    # denial) leaves the confirmation usable.
    reg.reserve(
        confirmation_id=conf.confirmation_id,
        tool_name="t",
        payload={"id": "A"},
        principal="u1",
    )
    reg.release(confirmation_id=conf.confirmation_id)
    assert (
        reg.reserve(
            confirmation_id=conf.confirmation_id,
            tool_name="t",
            payload={"id": "A"},
            principal="u1",
        )
        is not None
    )


# ---------------------------------------------------------------
# P1-6: journal bijection gaps
# ---------------------------------------------------------------


def test_attack_orphan_result_breaks_the_bijection():
    # An effect journaled with no pre-effect engagement.
    result = verify_intent_result_bijection(
        [{"causal_id": "c1", "syscall": "t"}],
        [
            {"syscall_id": "c1", "syscall": "t"},
            {"syscall_id": "c2", "syscall": "t"},
        ],
    )
    assert result.ok is False


def test_attack_syscall_swap_breaks_the_bijection():
    # Same causal id, different syscall between intent and result.
    result = verify_intent_result_bijection(
        [{"causal_id": "c1", "syscall": "mail.send"}],
        [{"syscall_id": "c1", "syscall": "vfs.write"}],
    )
    assert result.ok is False


# ---------------------------------------------------------------
# P1-7: replay authenticated against an arbitrary fingerprint
# ---------------------------------------------------------------


def test_attack_replay_cannot_authenticate_a_forged_commitment():
    os_ = CognitiveOS()
    run = os_.run("u1", {"risk": 0.1})
    ir = run.to_ir()
    with pytest.raises(RuntimeError, match="global_commitment mismatch"):
        os_.replay_verified(ir, expected_global_commitment="b" * 64)


def test_attack_replay_cannot_authenticate_without_an_anchor():
    os_ = CognitiveOS()
    run = os_.run("u1", {"risk": 0.1})
    ir = run.to_ir()
    # No external anchor at all is not a silent pass.
    with pytest.raises(TypeError):
        os_.replay_verified(ir)  # type: ignore[call-arg]


# ---------------------------------------------------------------
# P1-8: executor driven directly, bypassing policy
# ---------------------------------------------------------------


def test_attack_executor_cannot_be_driven_without_a_capability():
    executor = ToolExecutor(ToolRegistry())
    bare = ToolInvocation(tool_name="t", payload={}, process_id="p")
    result = SimpleNamespace(action_decision=SimpleNamespace(tool="t", tool_payload={}))
    with pytest.raises(UnauthorizedExecutionError):
        executor.execute_invocation(bare, result, SimpleNamespace(extra={}))  # type: ignore[arg-type]


def test_attack_forged_capability_is_refused():
    executor = ToolExecutor(ToolRegistry())
    foreign = InvocationAuthority()
    forged = foreign.authorize(
        ToolInvocation(tool_name="t", payload={}, process_id="p")
    )
    result = SimpleNamespace(action_decision=SimpleNamespace(tool="t", tool_payload={}))
    with pytest.raises(UnauthorizedExecutionError):
        executor.execute_invocation(forged, result, SimpleNamespace(extra={}))


def test_attack_no_public_executor_and_no_bypass():
    os_ = CognitiveOS()
    assert not hasattr(os_, "tool_executor")
    assert not hasattr(ToolExecutor(ToolRegistry()), "execute_authorized")
    assert not hasattr(os_, "replay")
