# tests/api/test_input_risk_doctrine_end_to_end.py
"""End-to-end acceptance of the input-risk doctrine (audit F-001-a5).

A caller-declared risk is untrusted input: it may harden the verdict,
never relax it, except for a payload exclusively dedicated to the risk
scalar under the graded posture. In production no relaxation happens at
all, pure payload included.
"""

from arvis import CognitiveOS, CognitiveOSConfig


def _decision(os_: CognitiveOS, payload: dict) -> str:
    return str(os_.run("acceptance", payload).to_dict()["decision"])


def _is_allowed(decision: str) -> bool:
    return "allowed=True" in decision


def _needs_confirmation(decision: str) -> bool:
    return "requires_user_validation=True" in decision


def test_mixed_payload_low_risk_is_never_allowed():
    # Audit F-001-a5 reproduction case: must not end ALLOW.
    decision = _decision(CognitiveOS(), {"action": "delete_everything", "risk": 0.1})
    assert not _is_allowed(decision)


def test_mixed_payload_high_risk_hardens():
    decision = _decision(CognitiveOS(), {"action": "wire_transfer", "risk": 0.98})
    assert not _is_allowed(decision)


def test_pure_payload_grading_is_preserved_outside_production():
    os_ = CognitiveOS()
    assert _is_allowed(_decision(os_, {"risk": 0.10}))
    medium = _decision(os_, {"risk": 0.55})
    assert _needs_confirmation(medium)
    assert not _is_allowed(_decision(os_, {"risk": 0.90}))


def test_production_pure_payload_never_relaxes():
    os_ = CognitiveOS(config=CognitiveOSConfig.production())
    decision = _decision(os_, {"risk": 0.10})
    assert not _is_allowed(decision)


def test_production_pure_payload_still_hardens():
    # Decision 2.2-a: hardening remains available in production.
    os_ = CognitiveOS(config=CognitiveOSConfig.production())
    decision = _decision(os_, {"risk": 0.95})
    assert not _is_allowed(decision)
