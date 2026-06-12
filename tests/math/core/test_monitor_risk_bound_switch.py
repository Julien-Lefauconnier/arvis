# tests/math/core/test_monitor_risk_bound_switch.py
"""The monitor's risk-bound switch: windowed Hoeffding vs cumulative CS.

Default is unchanged (windowed Hoeffding). The confidence-sequence mode tracks
the whole session: it does not forget early violations the way a sliding window
does, which is the point of an anytime-valid certificate.
"""

from __future__ import annotations

from typing import Any

import pytest

from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
    ScientificState,
)


def _bundle(confidence: float) -> Any:
    retrieval = type(
        "Retrieval",
        (),
        {"confidence": confidence, "scores": [], "semantic_roles": []},
    )()
    decision = type(
        "Decision", (), {"uncertainty_frames": [], "reason": "informational_query"}
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


def _drive(kind: str, n_violations: int, n_clean: int) -> Any:
    """n_violations risky turns (risk=1.0) then n_clean clean turns (risk≈0)."""
    core = ContractionMonitorCore(MonitorConfig(risk_bound=kind))
    state: dict[str, Any] | None = None
    snap: Any = None
    for i in range(n_violations + n_clean):
        snap, state = core.compute(_bundle(0.0 if i < n_violations else 0.95), state)
    return snap


def test_invalid_risk_bound_raises() -> None:
    with pytest.raises(ValueError):
        ContractionMonitorCore(MonitorConfig(risk_bound="bogus"))


def test_default_is_windowed_and_forgets_old_violations() -> None:
    # 50 violations then 250 clean turns: the 200-wide window no longer sees them.
    snap = _drive("hoeffding", n_violations=50, n_clean=250)
    assert snap.collapse_risk == 0.0


def test_confidence_sequence_is_cumulative() -> None:
    # Same sequence: the CS keeps the whole session -> 50 / 300.
    snap = _drive("confidence_sequence", n_violations=50, n_clean=250)
    assert snap.collapse_risk == pytest.approx(50.0 / 300.0, rel=1e-9)
    # The certified ceiling never under-reports the empirical rate.
    assert snap.risk_ucb + 1e-12 >= snap.collapse_risk
    assert 0.0 <= snap.risk_ucb <= 1.0


def test_cumulative_counter_survives_state_roundtrip() -> None:
    core = ContractionMonitorCore(MonitorConfig(risk_bound="confidence_sequence"))
    state: dict[str, Any] | None = None
    for _ in range(7):
        _snap, state = core.compute(_bundle(0.0), state)  # all violations
    assert state is not None
    assert state["risk_violations"] == 7
    # Round-trips through the opaque veramem<->arvis JSON blob.
    restored = ScientificState.from_dict(state)
    assert restored is not None
    assert restored.risk_violations == 7


def _drive_cs(boundary: str, n_clean: int) -> Any:
    """Drive only clean turns through the CS path with a given radius boundary."""
    core = ContractionMonitorCore(
        MonitorConfig(risk_bound="confidence_sequence", cs_boundary=boundary)
    )
    state: dict[str, Any] | None = None
    snap: Any = None
    for _ in range(n_clean):
        snap, state = core.compute(_bundle(0.95), state)
    return snap


def test_invalid_cs_boundary_raises() -> None:
    with pytest.raises(ValueError):
        ContractionMonitorCore(MonitorConfig(cs_boundary="bogus"))


def test_default_cs_boundary_is_fixed_lambda() -> None:
    assert MonitorConfig().cs_boundary == "fixed_lambda"


def test_stitched_boundary_informative_on_short_session() -> None:
    # Motivating finding: on a short clean session the fixed-lambda CS ceiling
    # stays near 1 (uninformative); the stitched ceiling is lower and usable.
    # Both still upper-bound the (zero) empirical violation rate.
    fixed = _drive_cs("fixed_lambda", n_clean=12)
    stitched = _drive_cs("stitched", n_clean=12)
    assert fixed.collapse_risk == 0.0
    assert stitched.collapse_risk == 0.0
    assert stitched.risk_ucb + 1e-12 >= stitched.collapse_risk
    assert stitched.risk_ucb < fixed.risk_ucb
    assert stitched.risk_ucb < 0.7
