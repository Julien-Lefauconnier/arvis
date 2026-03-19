# tests/contracts/test_signal_coercion_contract.py

import math
import pytest

from arvis.math.signals import RiskSignal, DriftSignal, UncertaintySignal
from arvis.math.signals.coercion import to_float, to_risk, to_drift, to_uncertainty


@pytest.mark.parametrize("value", [0.0, 0.2, 0.5, 1.0])
def test_signal_roundtrip(value):
    r = to_risk(value)
    d = to_drift(value)
    u = to_uncertainty(value)

    assert isinstance(r, RiskSignal)
    assert isinstance(d, DriftSignal)
    assert isinstance(u, UncertaintySignal)

    assert math.isclose(to_float(r), value)
    assert math.isclose(to_float(d), value)
    assert math.isclose(to_float(u), value)


def test_signal_idempotency():
    r = RiskSignal(0.42)

    r2 = to_risk(r)

    assert r is r2  # VERY IMPORTANT CONTRACT


def test_signal_clamping():
    r = to_risk(10.0)
    assert 0.0 <= to_float(r) <= 1.0

    r = to_risk(-5.0)
    assert 0.0 <= to_float(r) <= 1.0