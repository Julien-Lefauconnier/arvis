# tests/api/test_audit_commitment_policy.py

"""Audit commitment policy contract (F-015).

The absence of an audit commitment is never silent: every result view
carries the applied policy, a reason code when the commitment is
missing, and an explicit degradation flag under the DEGRADED policy.
Under REQUIRED, an unauditable run is refused.
"""

import pytest

from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.errors.base import ArvisSecurityError

_TIMELINE_COMMITMENT_CLS = "arvis.timeline.timeline_commitment.TimelineCommitment"


def _break_timeline_commitment(monkeypatch):
    monkeypatch.setattr(
        _TIMELINE_COMMITMENT_CLS + ".from_snapshot",
        classmethod(lambda cls, snapshot: (_ for _ in ()).throw(RuntimeError("boom"))),
    )


def test_nominal_run_has_commitment_and_clean_accounting():
    os = CognitiveOS()
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    assert view.global_commitment is not None
    assert view.commitment_policy == "degraded"
    assert view.commitment_reason is None
    assert view.commitment_degraded is False


def test_degraded_policy_records_reason_and_flag(monkeypatch):
    _break_timeline_commitment(monkeypatch)
    os = CognitiveOS()
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    assert view.global_commitment is None
    assert view.commitment_reason == "timeline_commitment_failure"
    assert view.commitment_degraded is True
    payload = view.to_dict()
    assert payload["commitment_policy"] == "degraded"
    assert payload["commitment_reason"] == "timeline_commitment_failure"
    assert payload["commitment_degraded"] is True


def test_required_policy_refuses_unauditable_run(monkeypatch):
    _break_timeline_commitment(monkeypatch)
    os = CognitiveOS(
        CognitiveOSConfig(
            audit_commitment_policy=AuditCommitmentPolicy.REQUIRED,
        )
    )
    with pytest.raises(ArvisSecurityError, match="timeline_commitment_failure"):
        os.run(user_id="u1", cognitive_input={"text": "hello"})


def test_optional_policy_records_reason_without_degradation(monkeypatch):
    _break_timeline_commitment(monkeypatch)
    os = CognitiveOS(
        CognitiveOSConfig(
            audit_commitment_policy=AuditCommitmentPolicy.OPTIONAL,
        )
    )
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    assert view.global_commitment is None
    assert view.commitment_reason == "timeline_commitment_failure"
    assert view.commitment_degraded is False
    assert view.commitment_policy == "optional"


def test_unserializable_ir_reason_code(monkeypatch):
    monkeypatch.setattr(
        "arvis.api.views.cognitive_result_view.build_ir_view",
        lambda state: {"bad": object()},
    )
    os = CognitiveOS()
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    assert view.global_commitment is None
    assert view.commitment_reason == "ir_not_serializable"
    assert view.commitment_degraded is True


def test_required_policy_passes_when_commitment_present():
    os = CognitiveOS(
        CognitiveOSConfig(
            audit_commitment_policy=AuditCommitmentPolicy.REQUIRED,
        )
    )
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    assert view.global_commitment is not None
    assert view.commitment_policy == "required"
    assert view.commitment_reason is None
