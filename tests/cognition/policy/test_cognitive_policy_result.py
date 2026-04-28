# tests/cognition/policy/test_cognitive_policy_result.py

from arvis.cognition.policy import CognitivePolicyResult


def test_policy_result_creation():
    r = CognitivePolicyResult(
        policy_name="attention",
        dimension="attention",
        suggestion_type="limit",
        rationale="too many items",
    )

    assert r.policy_name == "attention"


def test_policy_result_to_dict():
    r = CognitivePolicyResult(
        policy_name="test",
        dimension="dim",
        suggestion_type="suggest",
        rationale="reason",
    )

    d = r.to_dict()

    assert d["policy_name"] == "test"


def test_policy_result_immutable():
    r = CognitivePolicyResult("a", "b", "c", "d")

    try:
        r.policy_name = "x"
        assert False
    except Exception:
        assert True
