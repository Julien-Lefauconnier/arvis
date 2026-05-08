# tests/adapters/llm/test_llm_risk_signal.py

from arvis.adapters.llm.observability.risk_signal import LLMRiskSignal


def test_llm_risk_signal_defaults_to_zero():
    signal = LLMRiskSignal()

    assert signal.risk_pressure == 0.0
    assert signal.to_dict()["risk_pressure"] == 0.0


def test_llm_risk_signal_uses_max_pressure():
    signal = LLMRiskSignal(
        entropy_pressure=0.2,
        confidence_risk=0.7,
        variance_pressure=0.4,
        evaluation_risk=0.5,
        uncertainty_pressure=0.3,
    )

    assert signal.risk_pressure == 0.7


def test_llm_risk_signal_serializes_all_fields():
    signal = LLMRiskSignal(
        entropy_pressure=0.1,
        confidence_risk=0.2,
        variance_pressure=0.3,
        evaluation_risk=0.4,
        uncertainty_pressure=0.5,
    )

    assert signal.to_dict() == {
        "entropy_pressure": 0.1,
        "confidence_risk": 0.2,
        "variance_pressure": 0.3,
        "evaluation_risk": 0.4,
        "uncertainty_pressure": 0.5,
        "risk_pressure": 0.5,
    }
