# tests/uncertainty/test_uncertainty_inference_context.py
"""UncertaintyInference increment 2: the contextual gap is the conjunction of a
context-dependent query AND absent memory; it stacks with the referential gap."""

from __future__ import annotations

from arvis.reasoning.reasoning_gap import GapType
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_inference import UncertaintyInference


def test_context_dependent_with_absent_memory_fires() -> None:
    result = UncertaintyInference().infer(context_dependent=1.0, memory_present=False)
    assert len(result.frames) == 1
    assert UncertaintyAxis.CONTEXT_DEPENDENT in result.frames[0].axes
    assert result.gaps[0].gap_type == GapType.MISSING_CONTEXT


def test_memory_present_resolves_context() -> None:
    result = UncertaintyInference().infer(context_dependent=1.0, memory_present=True)
    assert result.frames == []
    assert result.gaps == []


def test_below_threshold_is_silent() -> None:
    result = UncertaintyInference().infer(context_dependent=0.0, memory_present=False)
    assert result.frames == []


def test_referential_and_contextual_stack() -> None:
    result = UncertaintyInference().infer(
        referential_ambiguity=1.0, context_dependent=1.0, memory_present=False
    )
    axes = {a for f in result.frames for a in f.axes}
    assert UncertaintyAxis.AMBIGUOUS_REFERENCE in axes
    assert UncertaintyAxis.CONTEXT_DEPENDENT in axes
    assert len(result.frames) == 2
