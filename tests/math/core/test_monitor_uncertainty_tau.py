# tests/math/core/test_monitor_uncertainty_tau.py
"""Decision-layer uncertainty axis in the contraction monitor.

A single fragility axis raises the Lyapunov energy but is below tau_uncertainty,
so it does NOT count as a violation: the certified-risk path (§6) is preserved.
Violations require fragility to STACK (>= 2 axes).
"""

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


def test_single_axis_lights_up_without_violation() -> None:
    core = ContractionMonitorCore(MonitorConfig())
    snap, _ = core.compute(_bundle(0.95, [_frame("ambiguous_reference")]), None)
    assert abs(snap.cur_lyap.uncertainty - 0.25) < 1e-9
    assert snap.cur_lyap.risk < 0.2  # grounded: orthogonal to uncertainty
    assert snap.collapse_risk == 0.0  # 1 axis < tau_uncertainty => no violation


def test_clean_turn_has_zero_uncertainty() -> None:
    core = ContractionMonitorCore(MonitorConfig())
    snap, _ = core.compute(_bundle(0.95, []), None)
    assert snap.cur_lyap.uncertainty == 0.0
    assert snap.collapse_risk == 0.0


def test_stacked_axes_trigger_violation() -> None:
    core = ContractionMonitorCore(MonitorConfig())
    frames = [_frame("ambiguous_reference", "context_dependent")]
    snap, _ = core.compute(_bundle(0.95, frames), None)
    assert snap.cur_lyap.uncertainty >= 0.5
    assert snap.collapse_risk > 0.0  # >= tau_uncertainty => violation


def test_tau_uncertainty_is_configurable() -> None:
    cfg = MonitorConfig(tau_uncertainty=0.2)
    snap, _ = ContractionMonitorCore(cfg).compute(
        _bundle(0.95, [_frame("ambiguous_reference")]), None
    )
    assert snap.collapse_risk > 0.0  # 0.25 >= 0.2 now violates
