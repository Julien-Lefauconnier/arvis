# tests/uncertainty/test_uncertainty_frame.py

import pytest

from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame


def test_uncertainty_frame_creation():
    frame = UncertaintyFrame(
        frame_id="TEST",
        label="Test frame",
        description="Test uncertainty",
        axes={UncertaintyAxis.CONTEXT_DEPENDENT},
    )

    assert frame.frame_id == "TEST"
    assert UncertaintyAxis.CONTEXT_DEPENDENT in frame.axes


def test_uncertainty_frame_axes_type():
    frame = UncertaintyFrame(
        frame_id="TEST",
        label="Test frame",
        description="Test uncertainty",
        axes={UncertaintyAxis.USER_SENSITIVE},
    )

    for axis in frame.axes:
        assert isinstance(axis, UncertaintyAxis)


def test_uncertainty_frame_is_frozen():
    frame = UncertaintyFrame(
        frame_id="TEST",
        label="Test frame",
        description="Test uncertainty",
        axes={UncertaintyAxis.DOMAIN_SPECIFIC},
    )

    with pytest.raises(AttributeError):
        frame.label = "Modified"
