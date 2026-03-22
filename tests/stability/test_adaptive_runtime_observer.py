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

    if result.is_available:
        assert result.kappa_eff is not None
        assert result.margin is not None
        assert result.regime in {"stable", "critical", "unstable"}
    else:
        assert result.kappa_eff is None
        assert result.margin is None
    assert result.regime in {"stable", "critical", "unstable"}


# --------------------------------------------------
# Mock estimator
# --------------------------------------------------

class DummySnap:
    def __init__(self, kappa_eff, is_available=True):
        self.kappa_eff = kappa_eff
        self.is_available = is_available


class DummyEstimator:
    def __init__(self, kappa_eff=None, margin=None, is_available=True):
        self._kappa_eff = kappa_eff
        self._margin = margin
        self._is_available = is_available

    def update(self, W_prev, W_next):
        return DummySnap(self._kappa_eff, self._is_available)

    def adaptive_switching_margin(self, J, tau_d):
        return self._margin


# --------------------------------------------------
# 1. Guard path (W_prev None)
# --------------------------------------------------

def test_guard_none_inputs():
    observer = AdaptiveRuntimeObserver(estimator=DummyEstimator())

    result = observer.update(
        W_prev=None,
        W_next=1.0,
        J=1.0,
        tau_d=1.0,
    )

    assert result.available is False
    assert result.margin is None
    assert result.kappa_eff is None
    assert result.regime == "critical"


# --------------------------------------------------
# 2. Guard path (W_prev <= 0)
# --------------------------------------------------

def test_guard_non_positive():
    observer = AdaptiveRuntimeObserver(estimator=DummyEstimator())

    result = observer.update(
        W_prev=0.0,
        W_next=1.0,
        J=1.0,
        tau_d=1.0,
    )

    assert result.available is False
    assert result.regime == "critical"


# --------------------------------------------------
# 3. Snap not available → margin None branch
# --------------------------------------------------

def test_snap_not_available():
    observer = AdaptiveRuntimeObserver(
        estimator=DummyEstimator(kappa_eff=0.5, is_available=False)
    )

    result = observer.update(
        W_prev=10.0,
        W_next=9.0,
        J=1.0,
        tau_d=1.0,
    )

    assert result.available is False
    assert result.margin is None
    assert result.regime == "critical"


# --------------------------------------------------
# 4. Stable regime (margin < 0)
# --------------------------------------------------

def test_stable_regime():
    observer = AdaptiveRuntimeObserver(
        estimator=DummyEstimator(kappa_eff=0.5, margin=-0.1)
    )

    result = observer.update(
        W_prev=10.0,
        W_next=9.0,
        J=1.0,
        tau_d=1.0,
    )

    assert result.available is True
    assert result.regime == "stable"
    assert result.margin == -0.1


# --------------------------------------------------
# 5. Critical regime (0 <= margin < 0.1)
# --------------------------------------------------

def test_critical_regime():
    observer = AdaptiveRuntimeObserver(
        estimator=DummyEstimator(kappa_eff=0.5, margin=0.05)
    )

    result = observer.update(
        W_prev=10.0,
        W_next=9.0,
        J=1.0,
        tau_d=1.0,
    )

    assert result.available is True
    assert result.regime == "critical"


# --------------------------------------------------
# 6. Unstable regime (margin >= 0.1)
# --------------------------------------------------

def test_unstable_regime():
    observer = AdaptiveRuntimeObserver(
        estimator=DummyEstimator(kappa_eff=0.5, margin=0.2)
    )

    result = observer.update(
        W_prev=10.0,
        W_next=9.0,
        J=1.0,
        tau_d=1.0,
    )

    assert result.available is True
    assert result.regime == "unstable"


# --------------------------------------------------
# 7. kappa_eff None → margin never computed
# --------------------------------------------------

def test_kappa_none():
    observer = AdaptiveRuntimeObserver(
        estimator=DummyEstimator(kappa_eff=None, margin=0.2)
    )

    result = observer.update(
        W_prev=10.0,
        W_next=9.0,
        J=1.0,
        tau_d=1.0,
    )

    assert result.margin is None
    assert result.regime == "critical"
    assert result.available is False