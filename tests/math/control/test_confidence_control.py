# tests/math/control/test_confidence_control.py

from arvis.math.control.confidence_control import (
    apply_confidence_control,
    ConfidenceControlInputs,
)


def test_epsilon_increases_when_confidence_low():
    low = apply_confidence_control(ConfidenceControlInputs(0.1, 0.2, 1.0))
    high = apply_confidence_control(ConfidenceControlInputs(0.9, 0.2, 1.0))

    assert low.epsilon > high.epsilon


def test_exploration_increases_when_confidence_low():
    low = apply_confidence_control(ConfidenceControlInputs(0.1, 0.2, 1.0))
    high = apply_confidence_control(ConfidenceControlInputs(0.9, 0.2, 1.0))

    assert low.exploration > high.exploration


def test_flags_triggered():
    out = apply_confidence_control(ConfidenceControlInputs(0.1, 0.2, 1.0))

    assert "low_confidence" in out.flags


def test_very_low_confidence_flag():
    out = apply_confidence_control(ConfidenceControlInputs(0.05, 0.2, 1.0))

    assert "very_low_confidence" in out.flags
