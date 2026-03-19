# tests/action/test_action_mapper.py


from arvis.action.action_mapper import map_verdict_to_action
from arvis.action.action_mode import ActionMode
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


# ---------------------------------------------------------
# 1. ABSTAIN → blocked action
# ---------------------------------------------------------

def test_map_verdict_abstain():
    decision = map_verdict_to_action(LyapunovVerdict.ABSTAIN)

    assert decision.allowed is False
    assert decision.requires_user_validation is False
    assert decision.denied_reason == "stability_guard"
    assert decision.audit_required is True
    assert decision.action_mode == ActionMode.MANUAL


# ---------------------------------------------------------
# 2. REQUIRE_CONFIRMATION → assisted action
# ---------------------------------------------------------

def test_map_verdict_requires_confirmation():
    decision = map_verdict_to_action(LyapunovVerdict.REQUIRE_CONFIRMATION)

    assert decision.allowed is True
    assert decision.requires_user_validation is True
    assert decision.denied_reason is None
    assert decision.audit_required is True
    assert decision.action_mode == ActionMode.ASSISTED


# ---------------------------------------------------------
# 3. ALLOW → automatic action
# ---------------------------------------------------------

def test_map_verdict_allow():
    decision = map_verdict_to_action(LyapunovVerdict.ALLOW)

    assert decision.allowed is True
    assert decision.requires_user_validation is False
    assert decision.denied_reason is None
    assert decision.audit_required is False
    assert decision.action_mode == ActionMode.AUTOMATIC


# ---------------------------------------------------------
# 4. Determinism (important invariant)
# ---------------------------------------------------------

def test_mapper_is_deterministic():
    decision_1 = map_verdict_to_action(LyapunovVerdict.ALLOW)
    decision_2 = map_verdict_to_action(LyapunovVerdict.ALLOW)

    assert decision_1 == decision_2


# ---------------------------------------------------------
# 5. No exception on unknown input (defensive safety)
# ---------------------------------------------------------

def test_mapper_handles_unknown_input_gracefully():
    class FakeVerdict:
        pass

    decision = map_verdict_to_action(FakeVerdict())

    # fallback should behave like ALLOW (default safe permissive)
    assert decision.allowed is True
    assert decision.action_mode == ActionMode.AUTOMATIC