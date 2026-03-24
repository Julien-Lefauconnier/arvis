# tests/adapters/ir/test_state_adapter.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.ir.state_adapter import StateIRAdapter


def test_state_adapter_builds_state_from_context() -> None:
    ctx = SimpleNamespace(
        bundle=SimpleNamespace(bundle_id="bundle-1"),
        collapse_risk=0.2,
        multi_horizon=SimpleNamespace(risk=0.11),
        global_forecast={"world_risk": 0.22},
        predictive_snapshot=SimpleNamespace(forecast_risk=0.33),
        global_stability={"fused_risk": 0.44},
        control_snapshot=SimpleNamespace(epsilon=0.55, smoothed_risk=0.66),
        drift_score=0.07,
        extra={"global_instability_warning": True},
        introspection="irg-state",
    )

    ir = StateIRAdapter.from_context(ctx)

    assert ir.bundle_id == "bundle-1"
    assert ir.dv == 0.07
    assert ir.collapse_risk.mh_risk == 0.11
    assert ir.collapse_risk.world_risk == 0.22
    assert ir.collapse_risk.forecast_risk == 0.33
    assert ir.collapse_risk.fused_risk == 0.44
    assert ir.collapse_risk.smoothed_risk == 0.66
    assert ir.epsilon == 0.55
    assert ir.early_warning is True
    assert ir.irg == "irg-state"


def test_state_adapter_falls_back_to_context_values() -> None:
    ctx = SimpleNamespace(
        bundle=SimpleNamespace(bundle_id="bundle-2"),
        collapse_risk=0.81,
        control_snapshot=None,
        drift_score=0.02,
        extra={},
    )

    ir = StateIRAdapter.from_context(ctx)

    assert ir.bundle_id == "bundle-2"
    assert ir.collapse_risk.fused_risk == 0.81
    assert ir.early_warning is True