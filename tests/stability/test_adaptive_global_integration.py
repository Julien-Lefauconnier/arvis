# tests/math/stability/test_adaptive_global_integration.py

from types import SimpleNamespace

from arvis.math.switching.global_stability_observer import GlobalStabilityObserver


def _params():
    return SimpleNamespace(
        J=1.1,
        alpha=0.3,
        gamma_z=1.0,
        eta=0.05,
        L_T=1.0,
    )


def test_global_stability_observer_includes_adaptive():
    obs = GlobalStabilityObserver()

    ctx1 = SimpleNamespace(
        w_current=10.0,
        switching_runtime=SimpleNamespace(
            total_switches=0,
            dwell_time=lambda: 10.0,
        ),
        switching_params=_params(),
    )

    ctx2 = SimpleNamespace(
        w_current=8.0,
        switching_runtime=SimpleNamespace(
            total_switches=1,
            dwell_time=lambda: 10.0,
        ),
        switching_params=_params(),
    )

    obs.update(ctx1)
    result = obs.update(ctx2)

    assert result.adaptive_kappa_eff is not None
    assert result.adaptive_margin is not None
    assert result.adaptive_regime in {"stable", "marginal", "unstable"}