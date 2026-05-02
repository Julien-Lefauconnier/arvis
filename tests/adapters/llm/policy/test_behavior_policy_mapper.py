# tests/adapters/llm/policy/test_behavior_policy_mapper.py

from arvis.adapters.llm.contracts.context import ARVISContext
from arvis.adapters.llm.policy.behavior_policy_mapper import LLMBehaviorPolicyMapper
from arvis.linguistic.acts.act_types import LinguisticActType


def test_behavior_policy_defaults_to_structured_information_for_stable_context() -> (
    None
):
    ctx = ARVISContext(
        risk_score=0.1,
        uncertainty_score=0.1,
        stability_score=0.9,
        confidence_score=0.9,
    )

    policy = LLMBehaviorPolicyMapper.from_arvis_context(ctx)

    assert policy.act == LinguisticActType.INFORMATION
    assert policy.temperature == 0.2
    assert policy.max_output_tokens == 512
    assert policy.allow_speculation is True
    assert policy.require_conservatism is False


def test_behavior_policy_becomes_conservative_under_uncertainty() -> None:
    ctx = ARVISContext(
        risk_score=0.2,
        uncertainty_score=0.8,
        stability_score=0.7,
        confidence_score=0.5,
    )

    policy = LLMBehaviorPolicyMapper.from_arvis_context(ctx)

    assert policy.act == LinguisticActType.INFORMATION
    assert policy.temperature == 0.1
    assert policy.max_output_tokens == 384
    assert policy.allow_speculation is False
    assert policy.allow_abstention is True
    assert "Avoid speculation." in policy.constraints


def test_behavior_policy_abstains_under_high_risk() -> None:
    ctx = ARVISContext(
        risk_score=0.9,
        uncertainty_score=0.4,
        stability_score=0.8,
        confidence_score=0.8,
    )

    policy = LLMBehaviorPolicyMapper.from_arvis_context(ctx)

    assert policy.act == LinguisticActType.ABSTENTION
    assert policy.temperature == 0.0
    assert policy.max_output_tokens == 256
    assert policy.require_conservatism is True


def test_behavior_policy_preserves_context_constraints() -> None:
    ctx = ARVISContext(
        risk_score=0.1,
        uncertainty_score=0.1,
        stability_score=0.9,
        confidence_score=0.9,
        constraints=["Never reveal private memory."],
    )

    policy = LLMBehaviorPolicyMapper.from_arvis_context(ctx)

    assert "Never reveal private memory." in policy.constraints
