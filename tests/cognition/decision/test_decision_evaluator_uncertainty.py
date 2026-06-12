# tests/cognition/decision/test_decision_evaluator_uncertainty.py
"""DecisionEvaluator surfaces referential uncertainty on the DecisionSignal."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from arvis.cognition.decision.decision_evaluator import DecisionEvaluator


def _ctx(intent: str, referential: float) -> Any:
    return SimpleNamespace(
        cognitive_input={"intent_type": intent, "referential_ambiguity": referential},
        memory_projection={},
    )


def test_ambiguous_query_emits_frame_and_gap() -> None:
    signal = DecisionEvaluator().evaluate(_ctx("question", 1.0))
    assert signal.reason == "informational_query"
    assert len(signal.uncertainty_frames) == 1
    assert len(signal.gaps) == 1


def test_clear_query_emits_nothing() -> None:
    signal = DecisionEvaluator().evaluate(_ctx("question", 0.0))
    assert signal.uncertainty_frames == []
    assert signal.gaps == []


def test_reason_mapping_unchanged() -> None:
    assert DecisionEvaluator().evaluate(_ctx("action", 0.0)).reason == "action_request"
    assert DecisionEvaluator().evaluate(_ctx("search", 0.0)).reason == "search"
    assert DecisionEvaluator().evaluate(_ctx("other", 0.0)).reason == "unknown"


def test_missing_feature_defaults_to_zero() -> None:
    ctx = SimpleNamespace(
        cognitive_input={"intent_type": "question"}, memory_projection={}
    )
    assert DecisionEvaluator().evaluate(ctx).uncertainty_frames == []
