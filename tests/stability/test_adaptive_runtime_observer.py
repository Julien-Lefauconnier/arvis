# tests/stability/test_adaptive_runtime_observer.py

from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator
from arvis.math.adaptive.adaptive_runtime_observer import AdaptiveRuntimeObserver


def test_adaptive_runtime_observer_basic():
    est = AdaptiveKappaEffEstimator()
    observer = AdaptiveRuntimeObserver(estimator=est)

    result = observer.update(
        W_prev=10.0,
        W_next=8.0,
        J=1.1,
        tau_d=10.0,
    )

    assert result["available"] is True
    assert result["kappa_eff"] is not None
    assert result["margin"] is not None
    assert result["regime"] in {"stable", "marginal", "unstable"}