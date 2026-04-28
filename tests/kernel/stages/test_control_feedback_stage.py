# tests/kernel/stages/test_control_feedback_stage.py

from types import SimpleNamespace

import pytest

from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot
from arvis.kernel.pipeline.stages.control_feedback_stage import ControlFeedbackStage

# --------------------------------------------------
# Dummy control result
# --------------------------------------------------


class DummyControl:
    def __init__(self, epsilon=1.0, exploration=1.0, flags=None):
        self.epsilon = epsilon
        self.exploration = exploration
        self.flags = flags or []


# --------------------------------------------------
# Fixtures
# --------------------------------------------------


def make_ctx():
    return SimpleNamespace(
        gate_result="ALLOW",
        control_snapshot=CognitiveControlSnapshot(
            gate_mode="test",
            epsilon=1.0,
            smoothed_risk=0.0,
            lyap_verdict="ALLOW",
            exploration=1.0,
            drift=0.0,
            regime="stable",
            calibration=None,
            temporal_pressure=None,
            temporal_modulation=None,
        ),
        system_confidence=0.5,
        extra={},
    )


# --------------------------------------------------
# 1. Early exit: no gate_result
# --------------------------------------------------


def test_skip_no_gate_result():
    ctx = make_ctx()
    ctx.gate_result = None

    stage = ControlFeedbackStage()
    stage.run(None, ctx)

    # no modification
    assert isinstance(ctx.control_snapshot, CognitiveControlSnapshot)


# --------------------------------------------------
# 2. Early exit: no control_snapshot
# --------------------------------------------------


def test_skip_no_snapshot():
    ctx = make_ctx()
    ctx.control_snapshot = None

    stage = ControlFeedbackStage()
    stage.run(None, ctx)

    assert ctx.control_snapshot is None


# --------------------------------------------------
# 3. Basic confidence control
# --------------------------------------------------


def test_basic_confidence(monkeypatch):
    ctx = make_ctx()

    def fake_control(inputs):
        return DummyControl(epsilon=0.8, exploration=0.9, flags=["low"])

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.control_feedback_stage.apply_confidence_control",
        fake_control,
    )

    stage = ControlFeedbackStage()
    stage.run(None, ctx)

    assert ctx.control_snapshot.epsilon == 0.8
    assert ctx.control_snapshot.exploration == 0.9
    assert ctx.extra["confidence_flags"] == ["low"]


# --------------------------------------------------
# 4. strong_decrease branch
# --------------------------------------------------


def test_strong_decrease(monkeypatch):
    ctx = make_ctx()
    ctx.extra["composite_gate_recommendation"] = "strong_decrease"

    def fake_control(inputs):
        return DummyControl(epsilon=1.0, exploration=1.0, flags=[])

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.control_feedback_stage.apply_confidence_control",
        fake_control,
    )

    ControlFeedbackStage().run(None, ctx)

    assert ctx.control_snapshot.epsilon == pytest.approx(0.8)
    assert ctx.control_snapshot.exploration == pytest.approx(0.7)
    assert "composite_strong_decrease" in ctx.extra["confidence_flags"]


# --------------------------------------------------
# 5. soft_decrease branch
# --------------------------------------------------


def test_soft_decrease(monkeypatch):
    ctx = make_ctx()
    ctx.extra["composite_gate_recommendation"] = "soft_decrease"

    def fake_control(inputs):
        return DummyControl(epsilon=1.0, exploration=1.0, flags=[])

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.control_feedback_stage.apply_confidence_control",
        fake_control,
    )

    ControlFeedbackStage().run(None, ctx)

    assert ctx.control_snapshot.epsilon == pytest.approx(0.9)
    assert "composite_soft_decrease" in ctx.extra["confidence_flags"]


# --------------------------------------------------
# 6. strong_increase branch
# --------------------------------------------------


def test_strong_increase(monkeypatch):
    ctx = make_ctx()
    ctx.extra["composite_gate_recommendation"] = "strong_increase"

    def fake_control(inputs):
        return DummyControl(epsilon=1.0, exploration=1.0, flags=[])

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.control_feedback_stage.apply_confidence_control",
        fake_control,
    )

    ControlFeedbackStage().run(None, ctx)

    assert ctx.control_snapshot.epsilon == pytest.approx(1.1)
    assert ctx.control_snapshot.exploration == pytest.approx(1.1)
    assert "composite_strong_increase" in ctx.extra["confidence_flags"]


# --------------------------------------------------
# 7. low confidence escalation
# --------------------------------------------------


def test_low_confidence_escalation(monkeypatch):
    ctx = make_ctx()

    def fake_control(inputs):
        return DummyControl(
            epsilon=1.0,
            exploration=1.0,
            flags=["very_low_confidence"],
        )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.control_feedback_stage.apply_confidence_control",
        fake_control,
    )

    ControlFeedbackStage().run(None, ctx)

    assert ctx.extra["low_confidence_escalation"] is True


# --------------------------------------------------
# 8. snapshot replacement
# --------------------------------------------------


def test_snapshot_replacement(monkeypatch):
    ctx = make_ctx()
    original = ctx.control_snapshot

    def fake_control(inputs):
        return DummyControl(epsilon=0.5, exploration=0.5, flags=[])

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.control_feedback_stage.apply_confidence_control",
        fake_control,
    )

    ControlFeedbackStage().run(None, ctx)

    assert ctx.control_snapshot is not original
