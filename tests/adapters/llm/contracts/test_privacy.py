# tests/adapters/llm/contracts/test_privacy.py

from arvis.adapters.llm.contracts.privacy import LLMPrivacyLevel


def test_enum_values():
    assert LLMPrivacyLevel.PUBLIC.value == "public"
    assert LLMPrivacyLevel.INTERNAL.value == "internal"
    assert LLMPrivacyLevel.SENSITIVE.value == "sensitive"
    assert LLMPrivacyLevel.CRITICAL.value == "critical"


def test_enum_comparison():
    assert LLMPrivacyLevel.PUBLIC != LLMPrivacyLevel.CRITICAL
