# tests/uncertainty/test_uncertainty_axis.py

from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.math.signals.uncertainty import UncertaintySignal


def test_uncertainty_axis_values():
    axes = list(UncertaintyAxis)

    assert len(axes) >= 5
    assert UncertaintyAxis.CONTEXT_DEPENDENT in axes
    assert UncertaintyAxis.HIGH_IMPACT in axes


def test_uncertainty_axis_string_values():
    assert UncertaintyAxis.CONTEXT_DEPENDENT.value == "context_dependent"
    assert isinstance(UncertaintyAxis.IRREVERSIBLE_RISK.value, str)


def test_uncertainty_level():
    s = UncertaintySignal(0.3)
    assert s.level() == 0.3


def test_uncertainty_is_high():
    assert UncertaintySignal(0.7).is_high() is True
    assert UncertaintySignal(0.69).is_high() is False


def test_uncertainty_repr():
    s = UncertaintySignal(0.123456)
    r = repr(s)

    assert "UncertaintySignal" in r
    assert "0.1235" in r  # arrondi à 4 décimales