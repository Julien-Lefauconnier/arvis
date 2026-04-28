# tests/conversation/test_memory_policy.py

from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict
from arvis.conversation.conversation_memory_policy import ConversationMemoryPolicy
from arvis.conversation.conversation_state import ConversationState
from arvis.conversation.response_strategy_resolver import ResponseStrategyResolver
from arvis.conversation.response_strategy_type import ResponseStrategyType


def test_memory_policy_keeps_strategy_without_constraints():
    state = ConversationState(
        signals={},
    )

    result = ConversationMemoryPolicy.apply(
        proposed_strategy=ResponseStrategyType.ACTION,
        state=state,
    )

    assert result == ResponseStrategyType.ACTION


def test_memory_policy_downgrades_action_when_constraints_present():
    state = ConversationState(
        signals={
            "constraints": ["no_marketing_emails"],
            "has_constraints": True,
        },
    )

    result = ConversationMemoryPolicy.apply(
        proposed_strategy=ResponseStrategyType.ACTION,
        state=state,
    )

    assert result == ResponseStrategyType.CONFIRMATION


def test_memory_policy_keeps_non_action_strategy():
    state = ConversationState(
        signals={
            "constraints": ["no_marketing_emails"],
            "has_constraints": True,
        },
    )

    result = ConversationMemoryPolicy.apply(
        proposed_strategy=ResponseStrategyType.INFORMATIONAL,
        state=state,
    )

    assert result == ResponseStrategyType.INFORMATIONAL


def test_resolver_applies_memory_guard_before_action():
    state = ConversationState(
        signals={
            "has_constraints": True,
            "constraints": ["no_marketing_emails"],
        }
    )

    decision = ResponseStrategyResolver.resolve(
        gate_verdict=CognitiveGateVerdict.ALLOW,
        has_decision=True,
        state=state,
    )

    assert decision.strategy == ResponseStrategyType.CONFIRMATION
    assert decision.reason == "memory_constraints_require_confirmation"


def test_resolver_keeps_action_when_no_memory_constraints():
    state = ConversationState(signals={})

    decision = ResponseStrategyResolver.resolve(
        gate_verdict=CognitiveGateVerdict.ALLOW,
        has_decision=True,
        state=state,
    )

    assert decision.strategy == ResponseStrategyType.ACTION


def test_resolver_keeps_informational_without_decision():
    state = ConversationState(signals={"has_constraints": True})

    decision = ResponseStrategyResolver.resolve(
        gate_verdict=CognitiveGateVerdict.ALLOW,
        has_decision=False,
        state=state,
    )

    assert decision.strategy == ResponseStrategyType.INFORMATIONAL
