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

    assert result.adaptive_kappa_eff is None or isinstance(
        result.adaptive_kappa_eff, float
    )
    assert result.adaptive_margin is not None
    assert result.adaptive_regime in {"stable", "marginal", "unstable"}


def _make_params(
    *,
    J: float = 1.0,
    alpha: float = 0.8,
    gamma_z: float = 0.1,
    eta: float = 0.5,
    L_T: float = 0.5,
):
    class Params:
        pass

    p = Params()
    p.J = J
    p.alpha = alpha
    p.gamma_z = gamma_z
    p.eta = eta
    p.L_T = L_T
    return p


def test_dwell_time_exception():
    obs = GlobalStabilityObserver()

    class Runtime:
        total_switches = 1

        def dwell_time(self):
            raise RuntimeError()

    ctx = type(
        "C",
        (),
        {
            "w_current": 1.0,
            "switching_runtime": Runtime(),
            "switching_params": _make_params(),
        },
    )()

    result = obs.update(ctx)

    assert result.tau_d == 0.0
    assert result.time == 1


def test_adaptive_observer_exception(monkeypatch):
    obs = GlobalStabilityObserver()
    obs._prev_W = 1.0

    class Runtime:
        total_switches = 1

        def dwell_time(self):
            return 1.0

    ctx = type(
        "C",
        (),
        {
            "w_current": 0.9,
            "switching_runtime": Runtime(),
            "switching_params": _make_params(),
        },
    )()

    monkeypatch.setattr(
        obs._adaptive_observer,
        "update",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError()),
    )

    result = obs.update(ctx)

    # fallback adaptatif activé
    assert result.adaptive_kappa_eff is not None
    assert result.adaptive_margin is not None
    assert result.adaptive_regime in {"stable", "critical", "unstable"}


def test_adaptive_fallback_regimes():
    obs = GlobalStabilityObserver()

    class Runtime:
        total_switches = 0

        def dwell_time(self):
            return 1.0

    ctx = type(
        "C",
        (),
        {
            "w_current": 1.0,
            "switching_runtime": Runtime(),
            "switching_params": _make_params(alpha=0.8, gamma_z=0.1, eta=0.5, L_T=0.5),
        },
    )()

    result = obs.update(ctx)

    # pas de _prev_W exploitable pour la partie adaptive => fallback
    assert result.adaptive_kappa_eff is not None
    assert result.adaptive_margin is not None
    assert result.adaptive_regime in {"stable", "critical", "unstable"}


def test_kappa_gap_exception(monkeypatch):
    obs = GlobalStabilityObserver()

    class Runtime:
        total_switches = 1

        def dwell_time(self):
            return 1.0

    ctx = type(
        "C",
        (),
        {
            "w_current": 1.0,
            "switching_runtime": Runtime(),
            "switching_params": _make_params(),
        },
    )()

    obs._prev_W = 1.2

    class BadAdaptive:
        kappa_eff = "boom"
        margin = 0.1
        regime = "unstable"

    monkeypatch.setattr(
        obs._adaptive_observer,
        "update",
        lambda **kwargs: BadAdaptive(),
    )

    result = obs.update(ctx)

    assert result.kappa_gap is None
    assert result.kappa_violation is False
