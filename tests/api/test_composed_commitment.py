# tests/api/test_composed_commitment.py
"""Composed v2 commitment and redaction before hash (F-007/F-018-a5).

The global commitment binds everything that governed a run and
everything the run did: cognitive IR, timeline, redacted syscall
journals, registry manifest fingerprint, effective configuration and
active policy tables. Content never enters the hashed journal in clear.
Replay recomposes from the declared commitment_inputs block (D-a), so
identical replay yields an identical commitment even on a divergent
environment, and the divergence stays detectable.
"""

from types import SimpleNamespace

from arvis import CognitiveOS
from arvis.api.commitment import (
    COMMITMENT_VERSION,
    REDACTION_POLICY_VERSION,
    compose_global_commitment,
    config_fingerprint,
    policies_fingerprint,
    redact_for_commitment,
    stable_hash,
    syscall_journal_digest,
)
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec


class _Probe(BaseTool):
    name = "commitment_probe"
    spec = ToolSpec(name="commitment_probe", description="probe")

    def execute(self, input_data):
        return {"ok": True}


# ---------------------------------------------------------------
# Redaction (F-018-a5)
# ---------------------------------------------------------------


def test_redaction_replaces_content_fields_with_digest_markers():
    entry = {
        "syscall": "tool.execute",
        "output": {"secret_document_body": "confidential"},
        "nested": {"payload": "raw content", "tick": 3},
    }
    redacted = redact_for_commitment(entry)
    assert redacted["syscall"] == "tool.execute"
    marker = redacted["output"]["__redacted__"]
    assert len(marker["sha256"]) == 64
    assert marker["policy"] == REDACTION_POLICY_VERSION
    assert "__redacted__" in redacted["nested"]["payload"]
    assert redacted["nested"]["tick"] == 3  # structure preserved


def test_redacted_journal_carries_no_source_content():
    intents = [{"kind": "syscall_intent", "syscall": "tool.execute"}]
    results = [
        {
            "syscall": "tool.execute",
            "result": {"body": "secret_document_body"},
            "output": "another_secret_string",
        }
    ]
    digest = syscall_journal_digest(intents, results)
    assert len(digest) == 64
    serialized = str(redact_for_commitment(results))
    assert "secret_document_body" not in serialized
    assert "another_secret_string" not in serialized


def test_redaction_digest_is_deterministic_and_content_sensitive():
    a = syscall_journal_digest([], [{"output": "content-a"}])
    a2 = syscall_journal_digest([], [{"output": "content-a"}])
    b = syscall_journal_digest([], [{"output": "content-b"}])
    assert a == a2
    assert a != b


def test_redaction_handles_non_serializable_content():
    class _Opaque:
        pass

    digest1 = syscall_journal_digest([], [{"result": _Opaque()}])
    digest2 = syscall_journal_digest([], [{"result": _Opaque()}])
    # Type identity only: deterministic across instances, no repr.
    assert digest1 == digest2


# ---------------------------------------------------------------
# Fingerprints
# ---------------------------------------------------------------


def test_config_fingerprint_is_sensitive_to_governance_fields():
    base = SimpleNamespace(
        enable_trace=True,
        strict_mode=False,
        runtime_mode="local",
        audit_commitment_policy="degraded",
        runtime_controls=None,
        consent_gate=None,
        egress_gate=None,
        audit_intent_sink=None,
        core_model=None,
        adapter_registry=None,
    )
    fp = config_fingerprint(base)
    assert fp == config_fingerprint(base)  # deterministic
    other = SimpleNamespace(**{**base.__dict__, "runtime_mode": "production"})
    assert config_fingerprint(other) != fp


def test_policies_fingerprint_is_stable():
    assert policies_fingerprint() == policies_fingerprint()
    assert len(policies_fingerprint()) == 64


def test_compose_embeds_the_version():
    inputs = {
        "registry_fingerprint": "r",
        "config_fingerprint": "c",
        "policies_fingerprint": "p",
        "syscall_journal_sha256": "s",
    }
    c1 = compose_global_commitment(
        ir_hash="i", timeline_commitment="t", commitment_inputs=inputs
    )
    # Recomposition with the explicit material must match, and the
    # version is part of the hashed material.
    material = {
        "commitment_version": COMMITMENT_VERSION,
        "ir_hash": "i",
        "timeline_commitment": "t",
        "config_fingerprint": "c",
        "policies_fingerprint": "p",
        "registry_fingerprint": "r",
        "syscall_journal_sha256": "s",
    }
    assert c1 == stable_hash(material)


# ---------------------------------------------------------------
# End-to-end: composition, sensitivity, replay (D-a)
# ---------------------------------------------------------------


def test_commitment_is_sensitive_to_the_registry_surface():
    # Same input, different registered surfaces: the composed
    # commitment differs even though the cognition is identical. This
    # closes the audit gap where the environment never entered the
    # commitment.
    plain = CognitiveOS()
    armed = CognitiveOS()
    armed.register_tool(_Probe())
    c_plain = plain.run("u1", {"risk": 0.1}).global_commitment
    c_armed = armed.run("u1", {"risk": 0.1}).global_commitment
    assert c_plain is not None and c_armed is not None
    assert c_plain != c_armed


def test_export_carries_the_commitment_inputs_block():
    os_ = CognitiveOS()
    view = os_.run("u1", {"risk": 0.1})
    exported = view.to_ir()
    block = exported["commitment_inputs"]
    assert set(block.keys()) == {
        "registry_fingerprint",
        "config_fingerprint",
        "policies_fingerprint",
        "syscall_journal_sha256",
    }
    ir_direct = os_.run_ir(user_id="u1", cognitive_input={"risk": 0.1})
    assert ir_direct == exported  # public contract: run_ir == to_ir


def test_replay_recomposes_identical_commitment():
    os_ = CognitiveOS()
    os_.register_tool(_Probe())
    r1 = os_.run("u1", {"risk": 0.1})
    r2 = os_.replay(r1.to_ir(), expected_global_commitment=r1.global_commitment)
    assert r2.global_commitment == r1.global_commitment


def test_replay_on_divergent_environment_holds_the_declared_commitment():
    # D-a: the replayer's environment never enters the recomposition;
    # the declared block travels with the IR, so the commitment holds,
    # and the divergence stays detectable by comparing the declared
    # block to the local environment.
    armed = CognitiveOS()
    armed.register_tool(_Probe())
    r1 = armed.run("u1", {"risk": 0.1})
    exported = r1.to_ir()

    plain = CognitiveOS()
    replayed = plain.replay(exported, expected_global_commitment=r1.global_commitment)
    assert replayed.global_commitment == r1.global_commitment

    local_registry_fp = plain.tool_registry.fingerprint()
    declared_registry_fp = exported["commitment_inputs"]["registry_fingerprint"]
    assert local_registry_fp != declared_registry_fp  # divergence detectable
