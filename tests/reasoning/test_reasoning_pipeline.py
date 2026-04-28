# tests/reasoning/test_reasoning_pipeline.py

from arvis.reasoning.reasoning_gap import ReasoningGap
from arvis.reasoning.reasoning_intent import ReasoningIntent


def test_reasoning_gap_to_intent_pipeline():
    gap = ReasoningGap(
        gap_type="missing_information",
        origin="test",
        severity=0.5,
        description="missing input data",
    )

    intent = ReasoningIntent(
        intent_type="clarify",
        reason="gap detected",
    )

    assert gap.severity > 0
    assert intent.intent_type == "clarify"
