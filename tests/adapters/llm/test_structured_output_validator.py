# tests/adapters/llm/test_structured_output_validator.py

from pydantic import BaseModel

from arvis.adapters.llm.validation.output_validator import (
    LLMOutputValidator,
    LLMValidationSeverity,
)


class IntentResult(BaseModel):
    intent: str
    confidence: float


def test_structured_output_accepts_valid_json() -> None:
    result = LLMOutputValidator.validate_structured(
        '{"intent": "search", "confidence": 0.9}',
        schema=IntentResult,
    )

    assert result.is_valid is True
    assert result.severity == LLMValidationSeverity.OK
    assert isinstance(result.parsed, IntentResult)
    assert result.parsed.intent == "search"


def test_structured_output_rejects_invalid_json() -> None:
    result = LLMOutputValidator.validate_structured(
        "not json",
        schema=IntentResult,
    )

    assert result.is_valid is False
    assert result.severity == LLMValidationSeverity.RETRYABLE
    assert result.errors[0].code == "invalid_json"


def test_structured_output_rejects_schema_mismatch() -> None:
    result = LLMOutputValidator.validate_structured(
        '{"intent": "search"}',
        schema=IntentResult,
    )

    assert result.is_valid is False
    assert result.severity == LLMValidationSeverity.RETRYABLE
    assert result.errors[0].code == "schema_validation_failed"
