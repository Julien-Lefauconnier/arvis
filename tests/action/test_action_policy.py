# tests/action/test_action_policy.py

from arvis.action.action_policy import ActionPolicy
from arvis.action.action_decision import ActionDecision
from arvis.math.signals import RiskSignal


def base_decision():
    return ActionDecision(
        allowed=True,
        requires_user_validation=False,
        denied_reason=None,
        audit_required=False,
        action_mode="execute",
    )


def test_policy_blocks_high_risk():
    policy = ActionPolicy(max_risk_threshold=0.8)

    decision = policy.apply(
        decision=base_decision(),
        risk=RiskSignal(0.9),
    )

    assert decision.allowed is False
    assert decision.denied_reason == "policy_risk_threshold"


def test_policy_forces_audit_mid_risk():
    policy = ActionPolicy(require_audit_above=0.5)

    decision = policy.apply(
        decision=base_decision(),
        risk=RiskSignal(0.6),
    )

    assert decision.audit_required is True


def test_policy_passthrough_low_risk():
    policy = ActionPolicy()

    decision = policy.apply(
        decision=base_decision(),
        risk=RiskSignal(0.2),
    )

    assert decision.allowed is True
    assert decision.audit_required is False