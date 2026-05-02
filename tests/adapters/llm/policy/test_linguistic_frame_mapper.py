# tests/adapters/llm/policy/test_linguistic_frame_mapper.py

from arvis.adapters.llm.contracts.context import ARVISContext
from arvis.adapters.llm.policy.behavior_policy_mapper import LLMBehaviorPolicyMapper
from arvis.adapters.llm.policy.linguistic_frame_mapper import LLMLinguisticFrameMapper


def test_linguistic_frame_is_derived_from_behavior_policy() -> None:
    ctx = ARVISContext(
        risk_score=0.7,
        uncertainty_score=0.8,
        stability_score=0.4,
        confidence_score=0.4,
    )

    policy = LLMBehaviorPolicyMapper.from_arvis_context(ctx)
    frame = LLMLinguisticFrameMapper.from_behavior_policy(policy)

    assert frame.act == policy.act
    assert frame.tone == policy.tone
    assert frame.verbosity == policy.verbosity
    assert frame.allow_speculation == policy.allow_speculation
    assert frame.constraints is not None
    assert "Avoid speculation." in frame.constraints
