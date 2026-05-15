# tests/errors/test_runtime_pipeline_errors.py

from arvis.errors import (
    PipelineExecutionContractViolation,
    PipelineRuntimeError,
)
from arvis.errors.base import (
    ArvisErrorSeverity,
    ErrorDomain,
)


def test_pipeline_runtime_error():
    error = PipelineRuntimeError("pipeline")

    assert error.domain == ErrorDomain.PIPELINE
    assert error.replay_safe is False


def test_pipeline_execution_contract_violation():
    error = PipelineExecutionContractViolation("contract")

    assert error.severity == ArvisErrorSeverity.FATAL
