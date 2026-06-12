# tests/cognition/decision/test_decision_evaluator_conflict.py
"""DecisionEvaluator attaches a conflict when an action targets an ambiguous
referent, and none for the same ambiguity in a question."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from arvis.cognition.decision.decision_evaluator import DecisionEvaluator


def _ctx(intent: str, referential: float) -> Any:
    return SimpleNamespace(
        cognitive_input={
            "intent_type": intent,
            "referential_ambiguity": referential,
        },
        memory_projection={},
    )


def test_ambiguous_action_emits_conflict() -> None:
    signal = DecisionEvaluator().evaluate(_ctx("action", 1.0))
    assert len(signal.conflicts) == 1
    assert len(signal.uncertainty_frames) == 2


def test_ambiguous_question_has_no_conflict() -> None:
    signal = DecisionEvaluator().evaluate(_ctx("question", 1.0))
    assert signal.conflicts == []
    assert len(signal.uncertainty_frames) == 1
