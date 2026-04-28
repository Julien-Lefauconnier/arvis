# tests/kernel/test_pi_impl.py

from arvis.kernel.projection.pi_impl import PiImpl


class DummyCtx:
    def __init__(self) -> None:
        self.system_tension = 42.0
        self.conflict_pressure = 12.5
        self.coherence_score = 0.8
        self.control_signal = 30.0
        self.adaptive_kappa_eff = 0.25
        self.predictive_snapshot = {"ok": True}
        self.projection_view = None


def test_pi_impl_projects_runtime_signals():
    ctx = DummyCtx()
    pi_impl = PiImpl()

    projected = pi_impl.project(ctx)
    view = projected.to_projection_view()

    assert projected.state_signals["system_tension"] == 42.0
    assert view["state.system_tension"] == 42.0
    assert view["risk.conflict_pressure"] == 12.5
    assert view["state.coherence_score"] == 0.8
    assert view["control.control_signal"] == 30.0
    assert view["trace.adaptive_kappa_eff"] == 0.25
