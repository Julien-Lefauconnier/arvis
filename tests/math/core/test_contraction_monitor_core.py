# tests/math/core/test_contraction_monitor_core.py
"""Unit tests for the v0 ContractionMonitorCore (certified contraction monitor)."""

from __future__ import annotations

import json
from typing import Any

from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
    MonitorSnapshot,
    ScientificState,
)
from arvis.math.lyapunov.lyapunov import LyapunovState


def _frame(n_axes: int) -> Any:
    return type("UncertaintyFrame", (), {"axes": set(range(n_axes))})()


def _bundle(
    *,
    confidence: float = 0.9,
    roles: tuple[str, ...] = (),
    n_axes: int = 0,
    reason: str = "informational_query",
    memory_pressure: float = 0.0,
) -> Any:
    retrieval = type(
        "RetrievalSnapshot",
        (),
        {"confidence": confidence, "scores": [], "semantic_roles": list(roles)},
    )()
    decision = type(
        "DecisionResult",
        (),
        {
            "uncertainty_frames": [_frame(n_axes)] if n_axes else [],
            "reason": reason,
        },
    )()
    return type(
        "Bundle",
        (),
        {
            "retrieval_snapshot": retrieval,
            "decision_result": decision,
            "memory_features": {"memory_pressure": memory_pressure},
        },
    )()


def _run(core: ContractionMonitorCore, bundles: list[Any]) -> list[MonitorSnapshot]:
    snapshots: list[MonitorSnapshot] = []
    state: ScientificState | None = None
    for bundle in bundles:
        snapshot, state = core.compute(bundle, state)
        snapshots.append(snapshot)
    return snapshots


def test_first_turn_is_neutral() -> None:
    core = ContractionMonitorCore()
    snapshot, nxt = core.compute(_bundle(), None)
    assert snapshot.delta_v == 0.0
    assert snapshot.drift_score == 0.0
    assert snapshot.prev_lyap is None
    assert nxt.turn_index == 0
    assert isinstance(snapshot.cur_lyap, LyapunovState)


def test_all_signals_bounded() -> None:
    core = ContractionMonitorCore()
    snapshot, _ = core.compute(
        _bundle(confidence=0.1, roles=("x",), n_axes=3, memory_pressure=2.0),
        None,
    )
    for value in (
        snapshot.collapse_risk,
        snapshot.drift_score,
        snapshot.energy_v,
        snapshot.risk_ucb,
        snapshot.cur_lyap.budget_used,
        snapshot.cur_lyap.risk,
        snapshot.cur_lyap.uncertainty,
        snapshot.cur_lyap.governance,
    ):
        assert 0.0 <= value <= 1.0
    assert snapshot.risk_ucb >= snapshot.collapse_risk


def test_nominal_session_has_zero_observed_risk() -> None:
    core = ContractionMonitorCore()
    bundles = [
        _bundle(confidence=0.95, roles=("author", "date"), n_axes=0) for _ in range(12)
    ]
    snaps = _run(core, bundles)
    assert all(s.collapse_risk == 0.0 for s in snaps)
    # The certified ceiling stays cautious until enough evidence accrues.
    assert all(s.risk_ucb >= s.collapse_risk for s in snaps)


def test_risky_session_drives_observed_risk_and_verdict() -> None:
    core = ContractionMonitorCore()
    bundles = [
        _bundle(confidence=0.1, roles=("x",), n_axes=2, reason="action_request")
        for _ in range(12)
    ]
    snaps = _run(core, bundles)
    assert snaps[-1].collapse_risk >= 0.9
    assert snaps[-1].risk_verdict == "CRITICAL"


def test_drift_zero_when_state_repeats_positive_when_it_shifts() -> None:
    core = ContractionMonitorCore()
    same = _bundle(confidence=0.9, roles=("a", "b"))
    snaps = _run(core, [same, same])
    assert snaps[1].drift_score == 0.0

    core2 = ContractionMonitorCore()
    shift = [
        _bundle(confidence=0.9, roles=("a", "b"), reason="search"),
        _bundle(
            confidence=0.3, roles=("c", "d", "e"), n_axes=1, reason="action_request"
        ),
    ]
    snaps2 = _run(core2, shift)
    assert snaps2[1].drift_score > 0.0
    assert snaps2[1].delta_v != 0.0


def test_governance_orders_intents() -> None:
    core = ContractionMonitorCore()
    action, _ = core.compute(_bundle(reason="action_request"), None)
    info, _ = core.compute(_bundle(reason="informational_query"), None)
    assert action.cur_lyap.governance > info.cur_lyap.governance


def test_serialization_round_trip_is_exact() -> None:
    core = ContractionMonitorCore()
    # turn 1 (prev_lyap is None), then turn 2 (populated windows)
    _, s1 = core.compute(_bundle(confidence=0.2, n_axes=1), None)
    _, s2 = core.compute(_bundle(confidence=0.8, roles=("r",)), s1)
    for state in (s1, s2):
        restored = ScientificState.from_dict(json.loads(json.dumps(state.to_dict())))
        assert restored == state


def test_from_dict_handles_empty() -> None:
    assert ScientificState.from_dict(None) is None
    assert ScientificState.from_dict({}) is None


def test_pure_transition_is_deterministic() -> None:
    core = ContractionMonitorCore()
    _, prior = core.compute(_bundle(confidence=0.4, roles=("a",), n_axes=1), None)
    bundle = _bundle(confidence=0.6, roles=("b",), reason="search")
    snap_a, next_a = core.compute(bundle, prior)
    snap_b, next_b = core.compute(bundle, prior)
    assert snap_a == snap_b
    assert next_a == next_b


def test_windows_are_bounded() -> None:
    cfg = MonitorConfig(risk_window=3, regime_window=3, regime_min_samples=2)
    core = ContractionMonitorCore(cfg)
    state: ScientificState | None = None
    for _ in range(6):
        _, state = core.compute(_bundle(confidence=0.1, n_axes=1), state)
    assert state is not None
    assert len(state.risk_window) <= 3
    assert len(state.regime_window) <= 3
