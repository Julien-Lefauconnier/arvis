# tests/cognition/decision/test_decision_evaluator.py
from __future__ import annotations

from types import SimpleNamespace

from arvis.cognition.decision.decision_evaluator import DecisionEvaluator


def _ctx(cognitive_input: object) -> SimpleNamespace:
    """Minimal context: evaluate() only reads cognitive_input + memory_projection."""
    return SimpleNamespace(cognitive_input=cognitive_input, memory_projection={})


def test_dict_intent_type_question_maps_to_informational_query() -> None:
    signal = DecisionEvaluator().evaluate(_ctx({"intent_type": "question"}))
    assert signal.reason == "informational_query"


def test_dict_intent_type_action_maps_to_action_request() -> None:
    signal = DecisionEvaluator().evaluate(_ctx({"intent_type": "action"}))
    assert signal.reason == "action_request"


def test_dict_intent_type_search_maps_to_search() -> None:
    signal = DecisionEvaluator().evaluate(_ctx({"intent_type": "search"}))
    assert signal.reason == "search"


def test_dict_without_intent_type_stays_unknown() -> None:
    signal = DecisionEvaluator().evaluate(_ctx({"query": "who are you?"}))
    assert signal.reason == "unknown"


def test_object_intent_type_still_supported() -> None:
    # Backward compatibility: an object exposing .intent_type still works.
    signal = DecisionEvaluator().evaluate(_ctx(SimpleNamespace(intent_type="question")))
    assert signal.reason == "informational_query"
