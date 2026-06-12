# tests/uncertainty/test_uncertainty_inference.py
"""UncertaintyInference (increment 1): referential ambiguity -> gap + frame."""

from __future__ import annotations

import pytest

from arvis.reasoning.reasoning_gap import GapType
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_inference import UncertaintyInference


def test_fires_above_threshold() -> None:
    result = UncertaintyInference(theta_ref=0.5).infer(referential_ambiguity=1.0)
    assert len(result.frames) == 1
    assert UncertaintyAxis.AMBIGUOUS_REFERENCE in result.frames[0].axes
    assert len(result.gaps) == 1
    assert result.gaps[0].gap_type == GapType.AMBIGUOUS_INTENT


def test_silent_below_threshold() -> None:
    result = UncertaintyInference(theta_ref=0.5).infer(referential_ambiguity=0.0)
    assert result.frames == []
    assert result.gaps == []


def test_threshold_is_inclusive() -> None:
    result = UncertaintyInference(theta_ref=0.5).infer(referential_ambiguity=0.5)
    assert len(result.frames) == 1


def test_rejects_invalid_theta() -> None:
    with pytest.raises(ValueError):
        UncertaintyInference(theta_ref=1.5)
