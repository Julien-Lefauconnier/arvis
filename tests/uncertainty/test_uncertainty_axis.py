# tests/uncertainty/test_uncertainty_axis.py

from arvis.uncertainty.uncertainty_axis import UncertaintyAxis


def test_uncertainty_axis_values():
    axes = list(UncertaintyAxis)

    assert len(axes) >= 5
    assert UncertaintyAxis.CONTEXT_DEPENDENT in axes
    assert UncertaintyAxis.HIGH_IMPACT in axes


def test_uncertainty_axis_string_values():
    assert UncertaintyAxis.CONTEXT_DEPENDENT.value == "context_dependent"
    assert isinstance(UncertaintyAxis.IRREVERSIBLE_RISK.value, str)