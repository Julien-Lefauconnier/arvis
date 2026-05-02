# tests/unit/llm/test_risk.py

from arvis.adapters.llm.governance.risk import LLMRisk, LLMRiskLevel


def test_risk_level():
    risk = LLMRisk(LLMRiskLevel.HIGH)

    assert risk.is_high()


def test_risk_allowed():
    risk = LLMRisk(LLMRiskLevel.MEDIUM)

    assert risk.is_allowed(LLMRiskLevel.HIGH)
    assert risk.is_allowed(LLMRiskLevel.MEDIUM)
    assert not risk.is_allowed(LLMRiskLevel.LOW)
