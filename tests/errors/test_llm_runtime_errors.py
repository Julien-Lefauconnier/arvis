# tests/errors/test_llm_runtime_errors.py

from arvis.errors.llm_runtime import (
    LLMEmptyResponseError,
    LLMExecutionContractViolation,
)


def test_llm_empty_response_error():
    error = LLMEmptyResponseError("empty")

    payload = error.to_dict()

    assert payload["domain"] == "llm"


def test_llm_execution_contract_violation():
    error = LLMExecutionContractViolation("bad")

    payload = error.to_dict()

    assert payload["replay_safe"] is False
