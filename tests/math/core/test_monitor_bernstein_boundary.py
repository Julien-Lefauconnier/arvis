# tests/math/core/test_monitor_bernstein_boundary.py
"""The bernstein CS boundary in the monitor: a clean grounded session reaches an
OK risk verdict far sooner than the stitched boundary, and the predictable
variance survives the cross-turn state round-trip."""

from __future__ import annotations

from typing import Any

import pytest

from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
    ScientificState,
)


def _clean_bundle() -> Any:
    retrieval = type(
        "Retrieval", (), {"confidence": 0.95, "scores": [], "semantic_roles": []}
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


def _turns_to_ok(boundary: str, n: int = 120) -> int | None:
    core = ContractionMonitorCore(
        MonitorConfig(risk_bound="confidence_sequence", cs_boundary=boundary)
    )
    prior = None
    for turn in range(n):
        snap, prior = core.compute(_clean_bundle(), prior)
        if snap.risk_verdict == "OK":
            return turn
    return None


def test_bernstein_reaches_ok_clean_session() -> None:
    ok = _turns_to_ok("bernstein")
    assert ok is not None and ok < 80


def test_bernstein_beats_stitched_on_clean_session() -> None:
    ok_b = _turns_to_ok("bernstein")
    ok_s = _turns_to_ok("stitched")
    assert ok_b is not None
    assert ok_s is None or ok_b < ok_s  # bernstein OK sooner (or stitched never)


def test_state_roundtrip_preserves_var_pred() -> None:
    state = ScientificState(
        prev_lyap=None,
        prev_roles=(),
        risk_window=(),
        regime_window=(),
        turn_index=3,
        risk_violations=1,
        risk_var_pred=0.42,
    )
    restored = ScientificState.from_dict(state.to_dict())
    assert restored is not None
    assert restored.risk_var_pred == 0.42


def test_monitor_rejects_unknown_cs_boundary() -> None:
    with pytest.raises(ValueError):
        ContractionMonitorCore(MonitorConfig(cs_boundary="nope"))
