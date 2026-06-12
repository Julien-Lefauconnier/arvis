# tests/math/core/test_monitor_uncertainty_stacking.py
"""Stacked uncertainty axes (referential + contextual) trigger the first
uncertainty-only violation: V crosses tau_uncertainty while risk stays low."""

from __future__ import annotations

from typing import Any

from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
)


def _frame(*axes: str) -> Any:
    return type("Frame", (), {"axes": set(axes)})()


def _bundle(confidence: float, frames: list[Any]) -> Any:
    retrieval = type(
        "Retrieval", (), {"confidence": confidence, "scores": [], "semantic_roles": []}
    )()
    decision = type(
        "Decision", (), {"uncertainty_frames": frames, "reason": "informational_query"}
    )()
    return type(
        "Bundle",
        (),
        {
            "retrieval_snapshot": retrieval,
            "decision_result": decision,
            "memory_features": {},
        },
    )()


def test_two_separate_frames_stack_and_violate() -> None:
    frames = [_frame("ambiguous_reference"), _frame("context_dependent")]
    snap, _ = ContractionMonitorCore(MonitorConfig()).compute(
        _bundle(0.95, frames), None
    )
    assert abs(snap.cur_lyap.uncertainty - 0.5) < 1e-9
    assert snap.cur_lyap.risk < 0.2  # grounded: violation is uncertainty-only
    assert snap.collapse_risk > 0.0


def test_single_contextual_axis_does_not_violate() -> None:
    snap, _ = ContractionMonitorCore(MonitorConfig()).compute(
        _bundle(0.95, [_frame("context_dependent")]), None
    )
    assert snap.collapse_risk == 0.0
