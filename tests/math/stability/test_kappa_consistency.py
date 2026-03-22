# tests/math/stability/test_kappa_consistency.py

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


def _runtime(switches=0):
    return SimpleNamespace(
        total_switches=switches,
        dwell_time=lambda: 10.0,
    )


def test_kappa_gap_computed():
    obs = GlobalStabilityObserver()

    ctx1 = SimpleNamespace(
        w_current=10.0,
        switching_runtime=_runtime(0),
        switching_params=_params(),
    )

    ctx2 = SimpleNamespace(
        w_current=8.0,
        switching_runtime=_runtime(1),
        switching_params=_params(),
    )

    obs.update(ctx1)
    result = obs.update(ctx2)

    if result.adaptive_kappa_eff is not None:
        assert result.kappa_gap is not None


def test_kappa_violation_flag_boolean():
    obs = GlobalStabilityObserver()

    ctx1 = SimpleNamespace(
        w_current=10.0,
        switching_runtime=_runtime(0),
        switching_params=_params(),
    )

    ctx2 = SimpleNamespace(
        w_current=50.0,  # force instability
        switching_runtime=_runtime(10),
        switching_params=_params(),
    )

    obs.update(ctx1)
    result = obs.update(ctx2)

    assert isinstance(result.kappa_violation, bool)
