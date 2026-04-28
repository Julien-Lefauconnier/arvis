# tests/action/test_action_evaluator.py

from arvis.action.action_evaluator import evaluate_action
from arvis.action.action_template import ActionTemplate
from arvis.math.signals import RiskSignal
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_high_risk_write_is_blocked():
    template = ActionTemplate(
        action_id="write",
        description="write data",
        writes_data=True,
    )

    decision = evaluate_action(
        verdict=LyapunovVerdict.ALLOW,
        template=template,
        risk=RiskSignal(0.9),
    )

    assert decision.allowed is False
    assert decision.denied_reason == "high_risk_write_block"


def test_external_action_requires_validation():
    template = ActionTemplate(
        action_id="external",
        description="call api",
        triggers_external=True,
    )

    decision = evaluate_action(
        verdict=LyapunovVerdict.ALLOW,
        template=template,
        risk=RiskSignal(0.5),
    )

    assert decision.requires_user_validation is True


def test_irreversible_action_requires_validation():
    template = ActionTemplate(
        action_id="delete",
        description="delete data",
        reversible=False,
    )

    decision = evaluate_action(
        verdict=LyapunovVerdict.ALLOW,
        template=template,
        risk=RiskSignal(0.3),
    )

    assert decision.requires_user_validation is True


def test_low_risk_allows_normal_behavior():
    template = ActionTemplate(
        action_id="read",
        description="read data",
    )

    decision = evaluate_action(
        verdict=LyapunovVerdict.ALLOW,
        template=template,
        risk=RiskSignal(0.1),
    )

    assert decision.allowed is True
    assert decision.requires_user_validation is False
