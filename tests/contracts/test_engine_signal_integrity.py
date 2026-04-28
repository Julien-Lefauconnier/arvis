# tests/contracts/test_engine_signal_integrity.py

from arvis.math.signals import RiskSignal, DriftSignal, UncertaintySignal
from arvis.math.signals.coercion import to_risk, to_drift, to_uncertainty


def test_engine_signal_types():
    r = to_risk(0.3)
    d = to_drift(0.1)
    u = to_uncertainty(0.5)

    assert isinstance(r, RiskSignal)
    assert isinstance(d, DriftSignal)
    assert isinstance(u, UncertaintySignal)
