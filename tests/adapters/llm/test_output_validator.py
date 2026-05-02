# tests/adapters/llm/test_output_validator.py

from arvis.adapters.llm.validation.output_validator import (
    LLMOutputValidator,
)


def test_valid_output_passes():
    result = LLMOutputValidator.validate("This is a valid answer.")
    assert result.is_valid
    assert result.errors == []


def test_empty_output_fails():
    result = LLMOutputValidator.validate("")
    assert not result.is_valid
    assert any(e.code == "empty_output" for e in result.errors)


def test_missing_abstention_detected():
    result = LLMOutputValidator.validate(
        "This is an answer.",
        require_abstention=True,
    )
    assert not result.is_valid
    assert any(e.code == "missing_abstention" for e in result.errors)


def test_abstention_detected():
    result = LLMOutputValidator.validate(
        "I don't have enough information to answer.",
        require_abstention=True,
    )
    assert result.is_valid


def test_cot_leak_detected():
    result = LLMOutputValidator.validate(
        "Let's think step by step. Step 1: analyze...",
    )
    assert not result.is_valid
    assert any(e.code == "cot_leak_detected" for e in result.errors)
