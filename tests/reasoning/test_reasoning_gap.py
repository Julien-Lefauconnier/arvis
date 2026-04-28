# tests/reasoning/test_reasoning_gap.py

from arvis.reasoning.reasoning_gap import ReasoningGap


def test_reasoning_gap_creation():
    gap = ReasoningGap(
        gap_type="missing_information",
        origin="test",
        severity=0.1,
        description="test gap",
    )

    assert gap.gap_type == "missing_information"
