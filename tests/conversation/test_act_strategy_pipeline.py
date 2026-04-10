# tests/conversation/test_act_strategy_pipeline.py

from arvis.conversation.conversation_orchestrator import ConversationOrchestrator
from arvis.conversation.conversation_context import ConversationContext
from arvis.conversation.conversation_state import ConversationState
from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict
from arvis.linguistic.acts.act_types import LinguisticActType


def build_context(
    verdict,
    has_decision=False,
    intent=None,
):
    return ConversationContext(
        prompt="test",
        act=None,
        gate_verdict=verdict,
        state=ConversationState(),
        has_decision=has_decision,
        intent_type=intent,
    )


def test_pipeline_abstention_flow():
    context = build_context(CognitiveGateVerdict.ABSTAIN)

    plan = ConversationOrchestrator.process(context)

    assert context.act is not None
    assert context.act.act_type == LinguisticActType.ABSTENTION
    assert plan.strategy.value == "abstention"


def test_pipeline_decision_flow():
    context = build_context(
        CognitiveGateVerdict.ALLOW,
        has_decision=True,
    )

    plan = ConversationOrchestrator.process(context)

    assert context.act.act_type == LinguisticActType.DECISION
    assert plan.strategy.value == "action"


def test_pipeline_information_flow():
    context = build_context(
        CognitiveGateVerdict.ALLOW,
        has_decision=False,
    )

    plan = ConversationOrchestrator.process(context)

    assert context.act.act_type == LinguisticActType.INFORMATION
    assert plan.strategy.value == "informational"


def test_pipeline_confirmation_flow():
    context = build_context(
        CognitiveGateVerdict.REQUIRE_CONFIRMATION,
    )

    plan = ConversationOrchestrator.process(context)

    assert context.act.act_type == LinguisticActType.REQUEST_CONFIRMATION
    assert plan.strategy.value == "confirmation"


def test_act_is_source_of_truth():
    context = build_context(CognitiveGateVerdict.ALLOW, has_decision=True)

    ConversationOrchestrator.process(context)

    # invariant critique ARVIS
    assert context.act is not None