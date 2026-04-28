# tests/uncertainty/test_uncertainty_registry.py

from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_frame_registry import UncertaintyFrameRegistry


def test_registry_contains_frames():
    frames = UncertaintyFrameRegistry.all()

    assert len(frames) >= 3


def test_registry_frames_have_axes():
    frames = UncertaintyFrameRegistry.all()

    for frame in frames:
        assert len(frame.axes) > 0
        for axis in frame.axes:
            assert isinstance(axis, UncertaintyAxis)


def test_registry_unique_ids():
    frames = UncertaintyFrameRegistry.all()

    ids = [f.frame_id for f in frames]

    assert len(ids) == len(set(ids))
