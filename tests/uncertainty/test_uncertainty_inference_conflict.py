# tests/uncertainty/test_uncertainty_inference_conflict.py
"""UncertaintyInference increment 3: internal conflict fires only for an action
request on an under-determined target. Orthogonal to grounding; questions never
conflict; memory resolves the contextual branch."""

from __future__ import annotations

from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_inference import UncertaintyInference


def _axes(result: object) -> set[UncertaintyAxis]:
    return {a for f in result.frames for a in f.axes}  # type: ignore[attr-defined]


def test_action_on_ambiguous_referent_conflicts() -> None:
    r = UncertaintyInference().infer(referential_ambiguity=1.0, reason="action_request")
    assert UncertaintyAxis.INTERNAL_CONFLICT in _axes(r)
    assert UncertaintyAxis.AMBIGUOUS_REFERENCE in _axes(r)
    assert len(r.conflicts) == 1


def test_question_on_ambiguous_referent_does_not_conflict() -> None:
    r = UncertaintyInference().infer(
        referential_ambiguity=1.0, reason="informational_query"
    )
    assert UncertaintyAxis.INTERNAL_CONFLICT not in _axes(r)
    assert r.conflicts == []


def test_clear_action_is_silent() -> None:
    r = UncertaintyInference().infer(referential_ambiguity=0.0, reason="action_request")
    assert r.frames == []
    assert r.conflicts == []


def test_action_on_missing_context_conflicts() -> None:
    r = UncertaintyInference().infer(
        context_dependent=1.0, memory_present=False, reason="action_request"
    )
    assert UncertaintyAxis.INTERNAL_CONFLICT in _axes(r)
    assert UncertaintyAxis.CONTEXT_DEPENDENT in _axes(r)


def test_action_with_resolving_memory_does_not_conflict() -> None:
    r = UncertaintyInference().infer(
        context_dependent=1.0, memory_present=True, reason="action_request"
    )
    assert r.frames == []
    assert r.conflicts == []
