# tests/uncertainty/test_uncertainty_to_intent_mapper.py


from arvis.uncertainty.uncertainty_to_intent_mapper import (
    UncertaintyToIntentMapper,
    map_uncertainty_to_intent,
)
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.reasoning.reasoning_intent import ReasoningIntentType


# ============================================================
# Helper
# ============================================================

def make_frame(axes):
    return UncertaintyFrame(
        frame_id="f1",
        label="test_frame",
        description="test_description",
        axes=set(axes),
    )


# ============================================================
# 1. HIGH IMPACT → REQUEST_USER_CLARIFICATION
# ============================================================

def test_high_impact_intent():
    frame = make_frame([UncertaintyAxis.HIGH_IMPACT])

    intents = UncertaintyToIntentMapper.map(frame)

    assert len(intents) == 1
    assert intents[0].intent_type == ReasoningIntentType.REQUEST_USER_CLARIFICATION
    assert "High-impact" in intents[0].reason


# ============================================================
# 2. IRREVERSIBLE RISK → REQUEST_USER_CLARIFICATION
# ============================================================

def test_irreversible_risk_intent():
    frame = make_frame([UncertaintyAxis.IRREVERSIBLE_RISK])

    intents = UncertaintyToIntentMapper.map(frame)

    assert len(intents) == 1
    assert intents[0].intent_type == ReasoningIntentType.REQUEST_USER_CLARIFICATION


# ============================================================
# 3. USER SENSITIVE → ALLOW_WEAK_ASSUMPTION
# ============================================================

def test_user_sensitive_intent():
    frame = make_frame([UncertaintyAxis.USER_SENSITIVE])

    intents = UncertaintyToIntentMapper.map(frame)

    assert len(intents) == 1
    assert intents[0].intent_type == ReasoningIntentType.ALLOW_WEAK_ASSUMPTION


# ============================================================
# 4. CONTEXT DEPENDENT → ALLOW_WEAK_ASSUMPTION
# ============================================================

def test_context_dependent_intent():
    frame = make_frame([UncertaintyAxis.CONTEXT_DEPENDENT])

    intents = UncertaintyToIntentMapper.map(frame)

    assert len(intents) == 1
    assert intents[0].intent_type == ReasoningIntentType.ALLOW_WEAK_ASSUMPTION


# ============================================================
# 5. PRIORITY: HIGH_IMPACT overrides USER_SENSITIVE
# ============================================================

def test_priority_high_over_sensitive():
    frame = make_frame([
        UncertaintyAxis.HIGH_IMPACT,
        UncertaintyAxis.USER_SENSITIVE,
    ])

    intents = UncertaintyToIntentMapper.map(frame)

    # if / elif → HIGH_IMPACT wins
    assert len(intents) == 1
    assert intents[0].intent_type == ReasoningIntentType.REQUEST_USER_CLARIFICATION


# ============================================================
# 6. NO MATCH → EMPTY
# ============================================================

def test_no_matching_axis():
    frame = make_frame([])

    intents = UncertaintyToIntentMapper.map(frame)

    assert intents == []


# ============================================================
# 7. PUBLIC API
# ============================================================

def test_function_api():
    frame = make_frame([UncertaintyAxis.HIGH_IMPACT])

    intents = map_uncertainty_to_intent(frame)

    assert len(intents) == 1