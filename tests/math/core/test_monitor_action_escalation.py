# tests/math/core/test_monitor_action_escalation.py
"""Same ambiguity, grounded turn: a question stays in caution (1 axis, no
violation) while an action escalates to abstention (2 axes -> violation) — the
violation is driven by uncertainty alone, with risk low."""

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
        "Decision", (), {"uncertainty_frames": frames, "reason": "action_request"}
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


def test_grounded_ambiguous_question_no_violation() -> None:
    snap, _ = ContractionMonitorCore(MonitorConfig()).compute(
        _bundle(0.95, [_frame("ambiguous_reference")]), None
    )
    assert snap.cur_lyap.risk < 0.2
    assert snap.collapse_risk == 0.0


def test_grounded_ambiguous_action_violates_on_uncertainty() -> None:
    frames = [_frame("ambiguous_reference"), _frame("internal_conflict")]
    snap, _ = ContractionMonitorCore(MonitorConfig()).compute(
        _bundle(0.95, frames), None
    )
    assert abs(snap.cur_lyap.uncertainty - 0.5) < 1e-9
    assert snap.cur_lyap.risk < 0.2  # grounded: violation is uncertainty-only
    assert snap.collapse_risk > 0.0
