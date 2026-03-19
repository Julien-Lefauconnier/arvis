# tests/contracts/test_signal_immutability.py

import pytest
from arvis.math.signals import RiskSignal


def test_signal_immutable():
    r = RiskSignal(0.5)

    with pytest.raises(Exception):
        r.value = 0.9