# tests/action/test_action_context_integration.py

from arvis.action.action_context import ActionContext
from arvis.action.action_evaluator import evaluate_action
from arvis.action.action_template import ActionTemplate
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.signals import RiskSignal


def test_strict_mode_forces_validation():
    template = ActionTemplate(
        action_id="read",
        description="read",
    )

    context = ActionContext(
        user_id="u1",
        responsibility_mode="strict",
    )

    decision = evaluate_action(
        verdict=LyapunovVerdict.ALLOW,
        template=template,
        risk=RiskSignal(0.1),
        context=context,
    )

    assert decision.requires_user_validation is True
    assert decision.audit_required is True


def test_autonomous_mode_allows_low_risk():
    template = ActionTemplate(
        action_id="read",
        description="read",
    )

    context = ActionContext(
        user_id="u1",
        responsibility_mode="autonomous",
    )

    decision = evaluate_action(
        verdict=LyapunovVerdict.ALLOW,
        template=template,
        risk=RiskSignal(0.1),
        context=context,
    )

    assert decision.allowed is True
    assert decision.requires_user_validation is False


def test_autonomous_mode_does_not_override_high_risk():
    template = ActionTemplate(
        action_id="write",
        description="write",
        writes_data=True,
    )

    context = ActionContext(
        user_id="u1",
        responsibility_mode="autonomous",
    )

    decision = evaluate_action(
        verdict=LyapunovVerdict.ALLOW,
        template=template,
        risk=RiskSignal(0.9),
        context=context,
    )

    assert decision.allowed is False
