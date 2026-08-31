# tests/api/test_default_core_monitor.py
"""The default engine measures its own science (campaign MATH-A, M1).

Until this campaign the default ``core_model`` was ``None``: every
default governed run carried constructor zeros instead of measurements,
and the Lyapunov machinery was evaluated only when a host supplied the
state (audit M1, 2026-08). Decision DM2: the contraction monitor is the
default core model; an explicit ``core_model=None`` remains the
opt-out. Decision DM1: the monitor measures the cognition only; the
caller-declared risk scalar stays governed by the input-risk gate and
never contaminates the measured axes.

These tests pin the wiring contract:

1. a default run measures (regime, risk ceiling, energy) instead of
   reporting absence;
2. final verdicts on pure declared-risk payloads are unchanged: the
   declared-risk gate keeps its authority (DM1);
3. explicit ``core_model=None`` still opts out entirely;
4. the default run stays deterministic, commitment included;
5. threading ``scientific_state`` across two runs advances the
   trajectory (turn index, previous fast state), which is what makes
   the delta-V gate live from the second turn on;
6. the monitor declares its calibration in a governance manifest, so
   the run commitment binds the actual thresholds, not just a class
   name.
"""

from __future__ import annotations

from typing import Any

from arvis import CognitiveOS, CognitiveOSConfig
from arvis.api.views.decision_status import DecisionStatus
from arvis.math.core.contraction_monitor_core import ContractionMonitorCore


def _run(engine: CognitiveOS, payload: Any, extra: dict[str, Any] | None = None) -> Any:
    return engine.run(user_id="m1", cognitive_input=payload, extra=extra)


def test_default_engine_measures_science() -> None:
    view = _run(CognitiveOS(), {"risk": 0.1})
    assert view.stability_view is not None, (
        "the default engine must measure; absence was the pre-M1 behavior"
    )
    assert view.stability_view.regime is not None
    assert view.stability_view.risk_level is not None
    assert view.stability_view.stability_score is not None


def test_pure_risk_final_verdicts_unchanged() -> None:
    """DM1: the measured science never relaxes nor hardens the declared
    risk policy on a pure-risk payload; the three bands hold."""
    expected = {
        0.1: DecisionStatus.ALLOWED,
        0.5: DecisionStatus.REQUIRES_CONFIRMATION,
        0.92: DecisionStatus.BLOCKED,
    }
    for declared, status in expected.items():
        view = _run(CognitiveOS(), {"risk": declared})
        assert view.status is status, (
            f"declared risk {declared} must stay {status.value}; the "
            f"monitor measures, the declared-risk gate governs (DM1)"
        )


def test_explicit_none_core_model_opts_out() -> None:
    engine = CognitiveOS(config=CognitiveOSConfig(core_model=None))
    view = _run(engine, {"risk": 0.1})
    assert view.stability_view is None, (
        "core_model=None is the documented opt-out and must reproduce "
        "the measure-nothing behavior"
    )


def test_default_run_is_deterministic() -> None:
    """Identical input, identical decision material. The trace block
    carries wall-clock timestamps by design and is excluded; the
    commitments and stability axes are the determinism that matters."""
    a = _run(CognitiveOS(), {"risk": 0.5}).to_dict()
    b = _run(CognitiveOS(), {"risk": 0.5}).to_dict()
    a.pop("trace", None)
    b.pop("trace", None)
    assert a == b, "wiring the monitor must not cost determinism"


def test_threaded_state_advances_the_trajectory() -> None:
    extra1: dict[str, Any] = {}
    _run(CognitiveOS(), {"risk": 0.3}, extra=extra1)
    state1 = extra1.get("scientific_state_next")
    assert isinstance(state1, dict), (
        "a default run must emit the replayable scientific state for the host to thread"
    )
    assert state1["turn_index"] == 0
    assert state1["prev_lyap"] is not None

    extra2: dict[str, Any] = {"scientific_state": state1}
    _run(CognitiveOS(), {"risk": 0.3}, extra=extra2)
    state2 = extra2.get("scientific_state_next")
    assert isinstance(state2, dict)
    assert state2["turn_index"] == 1, (
        "the second threaded turn must advance the trajectory; without "
        "this the delta-V gate can never become live"
    )
    assert len(state2["risk_window"]) == 2


def test_monitor_manifest_binds_calibration() -> None:
    manifest = ContractionMonitorCore().governance_manifest()
    assert manifest["component"] == "contraction_monitor_core"
    config = manifest["config"]
    for key in ("tau_risk", "risk_bound", "verdict_ok_ceiling", "regime_window"):
        assert key in config, (
            "the commitment must bind the monitor's actual calibration, "
            f"not just its class name (missing {key})"
        )
