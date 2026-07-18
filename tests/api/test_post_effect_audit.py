# tests/api/test_post_effect_audit.py
"""Mandatory post-effect audit and intent/result bijection (P0-1-a6).

The effect has happened; arvis cannot refuse it retroactively. What it
refuses is pretending to have proven it: a journaling failure after an
effect, or an effect intent without its paired result, yields no
commitment with the dedicated reason `audit_incomplete`. Under REQUIRED
the public result is refused through the existing absence machinery
(decision D4-b); under DEGRADED it is flagged. The bijection is
verified where the journals are read, in `_build_commitment_inputs`
(decision D4-c).
"""

import pytest

from arvis import CognitiveOS, CognitiveOSConfig
from arvis.api.audit import AuditCommitmentPolicy
from arvis.errors.base import ArvisSecurityError
from arvis.kernel_core.syscalls import syscall_handler as syscall_handler_module
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec


class _Probe(BaseTool):
    name = "audit_probe"
    spec = ToolSpec(name="audit_probe", description="probe")

    def execute(self, input_data):
        return {"ok": True}


@pytest.fixture
def broken_result_journal(monkeypatch):
    """Break the journal AFTER the effect: intents pass, results fail."""
    original = syscall_handler_module.SyscallHandler._journal

    def _broken(self, ctx, syscall, result, started_tick):
        raise RuntimeError("journal store down")

    monkeypatch.setattr(syscall_handler_module.SyscallHandler, "_journal", _broken)
    yield
    monkeypatch.setattr(syscall_handler_module.SyscallHandler, "_journal", original)


# ---------------------------------------------------------------
# Audit scenario reproduced, now closed
# ---------------------------------------------------------------


def test_required_commitment_fails_when_effect_result_journal_is_missing(
    broken_result_journal,
):
    # REQUIRED semantics, on a turn that actually reaches an effect
    # (llm.generate): in the production profile a pure {"risk": x}
    # payload hardens to ABSTAIN and no effect runs at all, so the
    # incompleteness machinery is exercised under a local REQUIRED
    # configuration where the turn is allowed and realized.
    os_ = CognitiveOS(
        config=CognitiveOSConfig(audit_commitment_policy=AuditCommitmentPolicy.REQUIRED)
    )
    with pytest.raises(ArvisSecurityError, match="audit_incomplete"):
        os_.run("u1", {"risk": 0.1})


def test_degraded_profile_flags_audit_incomplete(broken_result_journal):
    os_ = CognitiveOS()
    view = os_.run("u1", {"risk": 0.1})
    data = view.to_dict()
    assert view.global_commitment is None
    assert data["commitment_reason"] == "audit_incomplete"
    assert data["commitment_degraded"] is True
    assert data["audit_incomplete"] is True


def test_nominal_run_is_not_marked_incomplete():
    os_ = CognitiveOS()
    data = os_.run("u1", {"risk": 0.1}).to_dict()
    assert data["audit_incomplete"] is False
    assert data["commitment_reason"] is None


# ---------------------------------------------------------------
# Bijection (decision D4-c)
# ---------------------------------------------------------------


def test_effect_intent_and_result_are_bijectively_matched():
    os_ = CognitiveOS()
    os_.register_tool(_Probe())
    state, result = os_._execute(user_id="u1", cognitive_input={"risk": 0.1})
    execution_state = result.execution.execution_state
    intents = execution_state.syscall_intents
    journaled_ids = {
        entry.get("syscall_id") for entry in execution_state.syscall_results
    }
    assert intents, "an effect ran, an intent must exist"
    for intent in intents:
        assert intent["causal_id"] in journaled_ids


def test_orphan_intent_refuses_the_commitment():
    os_ = CognitiveOS()
    state, result = os_._execute(user_id="u1", cognitive_input={"risk": 0.1})
    execution_state = result.execution.execution_state
    execution_state.syscall_intents.append(
        {
            "kind": "syscall_intent",
            "syscall": "tool.execute",
            "causal_id": "syscall:orphan:never_journaled:0:0",
            "tick": 0,
            "process_id": "none",
        }
    )
    inputs, reason = os_._build_commitment_inputs(result)
    assert inputs is None
    assert reason == "audit_incomplete"


def test_handler_metadata_flag_refuses_the_commitment():
    os_ = CognitiveOS()
    state, result = os_._execute(user_id="u1", cognitive_input={"risk": 0.1})
    execution_state = result.execution.execution_state
    execution_state.metadata["audit_incomplete"] = True
    inputs, reason = os_._build_commitment_inputs(result)
    assert inputs is None
    assert reason == "audit_incomplete"


# --- campaign 5 (D-5): the a7 bijection gaps, now refused end to end ---


def test_orphan_result_refuses_the_commitment():
    # An effect journaled with no pre-effect engagement: a7 never
    # inspected result ids without a matching intent, so this passed.
    os_ = CognitiveOS()
    os_.register_tool(_Probe())
    state, result = os_._execute(user_id="u1", cognitive_input={"risk": 0.1})
    execution_state = result.execution.execution_state
    execution_state.syscall_results.append(
        {
            "syscall_id": "syscall:orphan_result:never_engaged:0:0",
            "causal_id": "syscall:orphan_result:never_engaged:0:0",
            "syscall": "tool.execute",
            "success": True,
        }
    )
    inputs, reason = os_._build_commitment_inputs(result)
    assert inputs is None
    assert reason == "audit_incomplete"


def test_duplicate_intent_refuses_the_commitment():
    # Two intents at one causal id: a7's set-membership check passed.
    os_ = CognitiveOS()
    os_.register_tool(_Probe())
    state, result = os_._execute(user_id="u1", cognitive_input={"risk": 0.1})
    execution_state = result.execution.execution_state
    intents = execution_state.syscall_intents
    assert intents, "an effect ran, an intent must exist"
    execution_state.syscall_intents.append(dict(intents[0]))
    inputs, reason = os_._build_commitment_inputs(result)
    assert inputs is None
    assert reason == "audit_incomplete"


def test_syscall_mismatch_refuses_the_commitment():
    # Intent and result at one causal id but different syscalls: a7
    # never compared the names.
    os_ = CognitiveOS()
    os_.register_tool(_Probe())
    state, result = os_._execute(user_id="u1", cognitive_input={"risk": 0.1})
    execution_state = result.execution.execution_state
    results = execution_state.syscall_results
    assert results, "an effect ran, a result must exist"
    results[0]["syscall"] = "some.other.syscall"
    inputs, reason = os_._build_commitment_inputs(result)
    assert inputs is None
    assert reason == "audit_incomplete"


# ---------------------------------------------------------------
# Handler-level behaviour
# ---------------------------------------------------------------


def test_effect_result_is_not_denied_retroactively(broken_result_journal):
    # The effect happened and its syscall-level outcome stands; the
    # refusal applies to the unprovable public restitution, never to
    # the effect itself.
    os_ = CognitiveOS()
    view = os_.run("u1", {"risk": 0.1})
    # The run completes and returns a view; only the commitment is
    # withheld.
    assert view.decision is not None


def test_replay_of_a_complete_run_still_verifies():
    os_ = CognitiveOS()
    os_.register_tool(_Probe())
    r1 = os_.run("u1", {"risk": 0.1})
    r2 = os_.replay(r1.to_ir(), expected_global_commitment=r1.global_commitment)
    assert r2.global_commitment == r1.global_commitment
