# tests/cognition/decision/test_decision_evaluator_context.py
"""DecisionEvaluator: contextual gap needs context-dependence AND absent memory."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from arvis.cognition.decision.decision_evaluator import DecisionEvaluator


def _ctx(context_dependent: float, memory: bool) -> Any:
    return SimpleNamespace(
        cognitive_input={
            "intent_type": "question",
            "context_dependent": context_dependent,
        },
        memory_projection=({"k": 1} if memory else {}),
    )


def test_context_dependent_without_memory_emits_frame() -> None:
    signal = DecisionEvaluator().evaluate(_ctx(1.0, memory=False))
    assert len(signal.uncertainty_frames) == 1


def test_memory_present_resolves() -> None:
    signal = DecisionEvaluator().evaluate(_ctx(1.0, memory=True))
    assert signal.uncertainty_frames == []
