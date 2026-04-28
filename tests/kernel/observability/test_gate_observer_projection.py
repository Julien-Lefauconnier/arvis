# tests/kernel/observability/test_gate_observer_projection.py

from types import SimpleNamespace

from arvis.kernel.observability.gate_observer import GateObserver


def test_gate_observer_exports_projection_trace():
    observer = GateObserver()

    ctx = SimpleNamespace(
        extra={"fusion_reasons": ["projection_lyapunov_incompatible"]},
        delta_w_history=[0.1, -0.2],
        projection_certificate=SimpleNamespace(
            domain_valid=True,
            is_projection_safe=False,
            lyapunov_compatibility_ok=False,
            margin_to_boundary=0.25,
            certification_level=SimpleNamespace(value="BASIC"),
        ),
        projection_view={"state.system_tension": 0.4},
        projection_view_raw={"state.system_tension": 5.0},
    )

    envelope = SimpleNamespace(
        hard_block=False,
        hard_reason=None,
        w_bound_ratio=1.01,
    )

    confidence_inputs = SimpleNamespace(
        delta_w=-0.2,
        global_safe=True,
        switching_safe=True,
        has_history=True,
        has_observability=True,
        collapse_risk=0.1,
    )

    observer.build(
        ctx,
        pre_verdict="ALLOW",
        final_verdict="REQUIRE_CONFIRMATION",
        delta_w=-0.2,
        w_prev=1.0,
        w_current=0.8,
        adaptive_metrics=None,
        switching_safe=True,
        global_safe=True,
        envelope=envelope,
        confidence_inputs=confidence_inputs,
        system_confidence=0.77,
        switching_metrics={"tau_d": 2.0},
        stability_certificate={"local": True},
        hard_block=False,
        hard_reason=None,
        w_ratio=1.01,
        recovery_detected=False,
        recovery_magnitude=None,
    )

    assert "projection_trace" in ctx.extra
    assert ctx.extra["projection_trace"]["available"] is True
    assert ctx.extra["projection_trace"]["domain_valid"] is True
    assert ctx.extra["projection_trace"]["safe"] is False
    assert ctx.extra["projection_trace"]["lyapunov_compatible"] is False
    assert ctx.extra["projection_trace"]["certification_level"] == "BASIC"

    assert "projection" in ctx.extra["fusion_trace"]
    assert ctx.extra["fusion_trace"]["projection"]["lyapunov_compatible"] is False

    assert "projection" in ctx.extra["theoretical_trace"]
    assert (
        ctx.extra["theoretical_trace"]["projection"]["raw_view"]["state.system_tension"]
        == 5.0
    )


def test_gate_observer_marks_projection_disturbance_flag():
    observer = GateObserver()

    ctx = SimpleNamespace(
        extra={
            "fusion_reasons": [],
            "projection_lyapunov_compatible": False,
        },
        delta_w_history=[],
        projection_certificate=None,
        projection_view=None,
        projection_view_raw=None,
    )

    envelope = SimpleNamespace(
        hard_block=False,
        hard_reason=None,
        w_bound_ratio=None,
    )

    confidence_inputs = SimpleNamespace(
        delta_w=0.1,
        global_safe=True,
        switching_safe=True,
        has_history=False,
        has_observability=True,
        collapse_risk=0.2,
    )

    observer.build(
        ctx,
        pre_verdict="ALLOW",
        final_verdict="REQUIRE_CONFIRMATION",
        delta_w=0.1,
        w_prev=1.0,
        w_current=1.1,
        adaptive_metrics=None,
        switching_safe=True,
        global_safe=True,
        envelope=envelope,
        confidence_inputs=confidence_inputs,
        system_confidence=0.42,
        switching_metrics={},
        stability_certificate={},
        hard_block=False,
        hard_reason=None,
        w_ratio=None,
        recovery_detected=False,
        recovery_magnitude=None,
    )

    assert ctx.extra["disturbance_signals"]["projection_lyapunov_incompatible"] is True
