# tests/kernel/pipeline/services/test_pipeline_llm_service.py

from __future__ import annotations

from types import SimpleNamespace

from pydantic import BaseModel

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.structured_output import (
    LLMStructuredOutputSpec,
)
from arvis.errors.base import (
    ArvisExternalError,
    ArvisRuntimeError,
)
from arvis.kernel.pipeline.services.pipeline_llm_service import (
    PipelineLLMService,
)
from arvis.kernel.pipeline.services.pipeline_retry_budget import (
    PipelineRetryBudget,
)
from arvis.kernel.pipeline.services.pipeline_retry_policy import (
    PipelineRetryPolicy,
)
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.syscall import SyscallResult
from tests.fixtures.builders.runtime_bindings_builder import (
    build_runtime_bindings,
)

_EXECUTE_LLM_SYSCALL = (
    "arvis.kernel.pipeline.services.pipeline_llm_service."
    "PipelineLLMService._execute_llm_syscall"
)


def _artifact(content: str) -> ExecutionArtifact:
    return ExecutionArtifact(
        artifact_type="llm_generation",
        syscall="llm.generate",
        status="success",
        output={"content": content},
        metadata={
            "prompt_logged": False,
        },
        replay_policy="journal_only_replay",
        process_id="proc-1",
        tick=None,
        timestamp=0.0,
        causal_id="causal-1",
    )


def _retryable_error() -> ArvisExternalError:
    return ArvisExternalError(
        "temporary outage",
        code="llm_execution_failed",
        details={
            "retry_class": "transient",
        },
    )


def _non_retryable_error() -> ArvisRuntimeError:
    return ArvisRuntimeError(
        "missing adapter",
        code="no_llm_adapter",
        retryable=False,
    )


def _success_result(content: str) -> SyscallResult:
    return SyscallResult(
        success=True,
        result=_artifact(content),
    )


def _success_result_with_llm_metadata() -> SyscallResult:
    return SyscallResult(
        success=True,
        result=ExecutionArtifact(
            artifact_type="llm_generation",
            syscall="llm.generate",
            status="success",
            output={"content": "ok"},
            metadata={
                "prompt_logged": False,
                "llm_observation": {
                    "entropy_mean": 0.8,
                    "confidence_mean": 0.2,
                    "logprob_variance": 0.1,
                },
                "llm_evaluation": {
                    "confidence": 0.2,
                    "uncertainty": 0.8,
                    "variance": 0.1,
                    "risk": 0.8,
                },
            },
            replay_policy="journal_only_replay",
            process_id="proc-1",
            tick=None,
            timestamp=0.0,
            causal_id="causal-1",
        ),
    )


def _request() -> LLMRequest:
    return LLMRequest(prompt="hello")


class DummyHandler:
    def handle(self, syscall):
        return _success_result("ok")


class StructuredIntentResult(BaseModel):
    intent: str
    confidence: float


class StructuredHandler:
    def handle(self, syscall):
        return _success_result('{"intent": "search", "confidence": 0.91}')


class FailingHandler:
    def handle(self, syscall):
        return SyscallResult.failure(
            ArvisRuntimeError(
                "llm failed",
                code="llm_failed",
            )
        )


class RetryThenSuccessHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, syscall):
        self.calls += 1

        if self.calls == 1:
            return SyscallResult.failure(_retryable_error())

        return _success_result("ok-after-retry")


class AlwaysRetryableFailureHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, syscall):
        self.calls += 1

        return SyscallResult.failure(_retryable_error())


class NonRetryableFailureHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, syscall):
        self.calls += 1

        return SyscallResult.failure(_non_retryable_error())


def test_pipeline_llm_service_returns_text() -> None:
    ctx = SimpleNamespace(
        extra={},
        runtime_bindings=build_runtime_bindings(
            syscall_handler=DummyHandler(),
        ),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="TestStage",
    )

    assert content == "ok"


def test_pipeline_llm_service_missing_handler_records_error() -> None:
    ctx = SimpleNamespace(extra={})

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="TestStage",
    )

    assert content is None

    error = ctx.extra["errors"][0]

    assert error["details"]["stage"] == "TestStage"
    assert error["details"]["llm_error"] == "missing_runtime_bindings"


def test_pipeline_llm_service_failure_records_error() -> None:
    ctx = SimpleNamespace(
        extra={},
        runtime_bindings=build_runtime_bindings(
            syscall_handler=FailingHandler(),
        ),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="TestStage",
    )

    assert content is None

    assert ctx.extra["errors"][0]["details"]["llm_error"] == "llm_failed"


def test_pipeline_llm_service_retries_retryable_failure_then_succeeds() -> None:
    handler = RetryThenSuccessHandler()

    ctx = SimpleNamespace(
        extra={},
        runtime_bindings=build_runtime_bindings(
            syscall_handler=handler,
        ),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="TestStage",
        retry_policy=PipelineRetryPolicy(max_attempts=2),
    )

    assert content == "ok-after-retry"
    assert handler.calls == 2

    event = ctx.extra["llm_retry_events"][0]

    assert event["retry"] is True
    assert event["error_code"] == "llm_execution_failed"
    assert event["reason"] == "retryable"

    assert ctx.extra["llm_retry_events"][1]["success"] is True


def test_pipeline_llm_service_stops_after_retry_limit() -> None:
    handler = AlwaysRetryableFailureHandler()

    ctx = SimpleNamespace(
        extra={},
        runtime_bindings=build_runtime_bindings(
            syscall_handler=handler,
        ),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="TestStage",
        retry_policy=PipelineRetryPolicy(max_attempts=3),
    )

    assert content is None
    assert handler.calls == 3

    assert ctx.extra["errors"][0]["details"]["llm_error"] == "llm_execution_failed"

    assert ctx.extra["llm_retry_events"][-1]["retry"] is False


def test_pipeline_llm_service_does_not_retry_non_retryable_failure() -> None:
    handler = NonRetryableFailureHandler()

    ctx = SimpleNamespace(
        extra={},
        runtime_bindings=build_runtime_bindings(
            syscall_handler=handler,
        ),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="TestStage",
        retry_policy=PipelineRetryPolicy(max_attempts=3),
    )

    assert content is None
    assert handler.calls == 1

    assert ctx.extra["errors"][0]["details"]["llm_error"] == "no_llm_adapter"

    assert ctx.extra["llm_retry_events"][0]["retry"] is False


def test_pipeline_llm_service_stops_when_retry_budget_exhausted() -> None:
    handler = AlwaysRetryableFailureHandler()

    ctx = SimpleNamespace(
        extra={},
        runtime_bindings=build_runtime_bindings(
            syscall_handler=handler,
        ),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="TestStage",
        retry_policy=PipelineRetryPolicy(max_attempts=3),
        retry_budget=PipelineRetryBudget(max_retries=1),
    )

    assert content is None
    assert handler.calls == 2

    final_event = ctx.extra["llm_retry_events"][-1]

    assert final_event["retry"] is False
    assert final_event["budget_allowed"] is False
    assert final_event["budget_reason"] == "retry_budget_exhausted"


def test_llm_service_retries_until_success(mocker):
    ctx = SimpleNamespace(
        extra={
            "_allow_mock_runtime": True,
        },
        runtime_bindings=build_runtime_bindings(
            syscall_handler=object(),
        ),
    )

    calls = []

    def fake_call(*args, **kwargs):
        if len(calls) < 2:
            calls.append("fail")
            return SyscallResult.failure(_retryable_error())

        return _success_result("ok")

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        side_effect=fake_call,
    )

    result = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        retry_policy=PipelineRetryPolicy(max_attempts=5),
    )

    assert result == "ok"
    assert len(calls) == 2


def test_llm_service_applies_delay(mocker):
    ctx = SimpleNamespace(
        extra={
            "_allow_mock_runtime": True,
        },
        runtime_bindings=build_runtime_bindings(
            syscall_handler=object(),
        ),
    )

    sleep_mock = mocker.patch(
        "arvis.kernel.pipeline.services.pipeline_llm_service.PipelineLLMService._sleep"
    )

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        return_value=SyscallResult.failure(_retryable_error()),
    )

    PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        retry_policy=PipelineRetryPolicy(
            max_attempts=2,
            base_delay_ms=100,
        ),
    )

    sleep_mock.assert_called_once_with(100)


def test_llm_service_stops_when_budget_exhausted(mocker):
    ctx = SimpleNamespace(
        extra={
            "_allow_mock_runtime": True,
        },
        runtime_bindings=build_runtime_bindings(
            syscall_handler=object(),
        ),
    )

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        return_value=SyscallResult.failure(_retryable_error()),
    )

    result = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        retry_policy=PipelineRetryPolicy(max_attempts=5),
        retry_budget=PipelineRetryBudget(max_retries=0),
    )

    assert result is None


def test_llm_service_no_retry_on_permanent_error(mocker):
    ctx = SimpleNamespace(
        extra={
            "_allow_mock_runtime": True,
        },
        runtime_bindings=build_runtime_bindings(
            syscall_handler=object(),
        ),
    )

    error = ArvisExternalError(
        "fail",
        code="x",
        details={
            "retry_class": "permanent",
        },
    )

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        return_value=SyscallResult.failure(error),
    )

    result = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        retry_policy=PipelineRetryPolicy(max_attempts=5),
    )

    assert result is None


def test_pipeline_llm_service_records_structured_output() -> None:
    ctx = SimpleNamespace(
        extra={},
        runtime_bindings=build_runtime_bindings(
            syscall_handler=StructuredHandler(),
        ),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(
            prompt="hello",
            structured_output=LLMStructuredOutputSpec(
                schema_name="StructuredIntentResult",
                schema=StructuredIntentResult,
            ),
        ),
        stage="IntentStage",
    )

    assert content == '{"intent": "search", "confidence": 0.91}'

    parsed = ctx.extra["llm_structured_outputs"]["IntentStage"]

    assert parsed.intent == "search"
    assert parsed.confidence == 0.91


def test_pipeline_llm_service_records_llm_runtime_metadata(
    mocker,
) -> None:
    ctx = SimpleNamespace(
        extra={
            "_allow_mock_runtime": True,
        },
        runtime_bindings=build_runtime_bindings(
            syscall_handler=object(),
        ),
    )

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        return_value=_success_result_with_llm_metadata(),
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        stage="LLMStage",
    )

    assert content == "ok"

    assert ctx.extra["llm_observation"]["entropy_mean"] == 0.8

    assert ctx.extra["llm_evaluation"]["confidence"] == 0.2

    assert ctx.extra["llm_evaluation"]["risk"] == 0.8


def test_pipeline_llm_service_records_runtime_metadata_into_execution_state():
    from arvis.kernel.execution.cognitive_execution_state import (
        CognitiveExecutionState,
    )
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )

    ctx = CognitivePipelineContext(
        user_id="u1",
        cognitive_input=None,
        legacy_execution_state=CognitiveExecutionState(),
    )

    result = SyscallResult(
        success=True,
        result=ExecutionArtifact(
            artifact_type="llm_generation",
            syscall="llm.generate",
            status="success",
            output={"content": "ok"},
            metadata={
                "llm_observation": {
                    "confidence_mean": 0.8,
                    "entropy_mean": 0.2,
                },
                "llm_evaluation": {
                    "risk": 0.2,
                    "uncertainty": 0.2,
                },
            },
            replay_policy="journal_only_replay",
            timestamp=123.0,
        ),
    )

    PipelineLLMService._record_llm_runtime_metadata(
        ctx,
        result,
    )

    assert ctx.extra["llm_observation"]["confidence_mean"] == 0.8

    assert ctx.extra["llm_evaluation"]["risk"] == 0.2

    assert ctx.execution_state is not None

    assert ctx.execution_state.llm.observation == ctx.extra["llm_observation"]

    assert ctx.execution_state.llm.evaluation == ctx.extra["llm_evaluation"]
