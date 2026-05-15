# tests/errors/test_runtime_execution_errors.py

from arvis.errors.runtime_execution import (
    ProcessExecutionAborted,
    RuntimeExecutionContractViolation,
)


def test_process_execution_aborted_metadata():
    error = ProcessExecutionAborted("boom")

    payload = error.to_dict()

    assert payload["type"] == "ProcessExecutionAborted"
    assert payload["replay_safe"] is False


def test_runtime_execution_contract_violation():
    error = RuntimeExecutionContractViolation("invalid")

    payload = error.to_dict()

    assert payload["severity"] == "fatal"
