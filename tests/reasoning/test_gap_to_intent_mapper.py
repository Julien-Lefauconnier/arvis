# tests/reasoning/test_gap_to_intent_mapper.py


from arvis.reasoning.gap_to_intent_mapper import GapToIntentMapper
from arvis.reasoning.reasoning_gap import GapType, ReasoningGap
from arvis.reasoning.reasoning_intent import ReasoningIntentType

# ============================================================
# Helper
# ============================================================


def make_gap(
    gap_type,
    description="desc",
    origin="system",
    origin_ref="origin",
    severity=0.5,
):
    return ReasoningGap(
        gap_type=gap_type,
        description=description,
        origin=origin,
        origin_ref=origin_ref,
        severity=severity,
    )


# ============================================================
# 1. MISSING_CONTEXT → REQUEST_USER_CLARIFICATION
# ============================================================


def test_missing_context_maps_to_intent():
    gap = make_gap(GapType.MISSING_CONTEXT)

    intents = GapToIntentMapper.map(gap)

    assert len(intents) == 1
    intent = intents[0]

    assert intent.intent_type == ReasoningIntentType.REQUEST_USER_CLARIFICATION
    assert intent.reason == "desc"
    assert intent.source_ref == "origin"


# ============================================================
# 2. OTHER GAP → EMPTY
# ============================================================


def test_other_gap_returns_empty():
    # prendre un autre type valide
    other_type = next(g for g in GapType if g != GapType.MISSING_CONTEXT)

    gap = make_gap(other_type)

    intents = GapToIntentMapper.map(gap)

    assert intents == []


# ============================================================
# 3. EDGE: EMPTY DESCRIPTION
# ============================================================


def test_missing_context_empty_description():
    gap = make_gap(GapType.MISSING_CONTEXT, description="")

    intents = GapToIntentMapper.map(gap)

    assert len(intents) == 1
    assert intents[0].reason == ""
