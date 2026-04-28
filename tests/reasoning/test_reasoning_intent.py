# tests/reasoning/test_reasoning_intent.py

from arvis.reasoning.reasoning_intent import ReasoningIntent


def test_reasoning_intent_creation():
    intent = ReasoningIntent(
        intent_type="clarify",
        reason="missing data",
    )

    assert intent.intent_type == "clarify"
