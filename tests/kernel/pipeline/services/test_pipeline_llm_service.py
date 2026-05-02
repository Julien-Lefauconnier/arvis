# tests/kernel/pipeline/services/test_pipeline_llm_service.py

from __future__ import annotations

from types import SimpleNamespace

from pydantic import BaseModel

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.structured_output import LLMStructuredOutputSpec
from arvis.kernel.pipeline.services.pipeline_llm_service import PipelineLLMService
from arvis.kernel.pipeline.services.pipeline_retry_budget import PipelineRetryBudget
from arvis.kernel.pipeline.services.pipeline_retry_policy import PipelineRetryPolicy
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.errors import SyscallError
from arvis.kernel_core.syscalls.syscall import SyscallResult

_EXECUTE_LLM_SYSCALL = (
    "arvis.kernel.pipeline.services.pipeline_llm_service."
    "PipelineLLMService._execute_llm_syscall"
)


class DummyHandler:
    def handle(self, syscall):
        return SyscallResult(
            success=True,
            result=ExecutionArtifact(
                artifact_type="llm_generation",
                syscall="llm.generate",
                status="success",
                output={
                    "content": "ok",
                },
                metadata={
                    "prompt_logged": False,
                },
                replay_policy="journal_only_replay",
                process_id="proc-1",
                tick=None,
                timestamp=0.0,
                causal_id="causal-1",
            ),
        )


class StructuredIntentResult(BaseModel):
    intent: str
    confidence: float


class StructuredHandler:
    def handle(self, syscall):
        return _success_result('{"intent": "search", "confidence": 0.91}')


class FailingHandler:
    def handle(self, syscall):
        return SyscallResult(
            success=False,
            error="llm_failed",
        )


class RetryThenSuccessHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, syscall):
        self.calls += 1

        if self.calls == 1:
            return SyscallResult.failure(
                SyscallError(
                    code="llm_execution_failed",
                    message="temporary outage",
                    retryable=True,
                )
            )

        return SyscallResult(
            success=True,
            result=ExecutionArtifact(
                artifact_type="llm_generation",
                syscall="llm.generate",
                status="success",
                output={"content": "ok-after-retry"},
                metadata={"prompt_logged": False},
                replay_policy="journal_only_replay",
                process_id="proc-1",
                tick=None,
                timestamp=0.0,
                causal_id="causal-1",
            ),
        )


class AlwaysRetryableFailureHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, syscall):
        self.calls += 1

        return SyscallResult.failure(
            SyscallError(
                code="llm_execution_failed",
                message="temporary outage",
                retryable=True,
            )
        )


class NonRetryableFailureHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, syscall):
        self.calls += 1

        return SyscallResult.failure(
            SyscallError(
                code="no_llm_adapter",
                message="missing adapter",
                retryable=False,
            )
        )


def _request() -> LLMRequest:
    return LLMRequest(prompt="hello")


def _retryable_error() -> SyscallError:
    return SyscallError(
        code="llm_execution_failed",
        message="temporary outage",
        retryable=True,
    )


def _success_result(content: str) -> SyscallResult:
    return SyscallResult(
        success=True,
        result=ExecutionArtifact(
            artifact_type="llm_generation",
            syscall="llm.generate",
            status="success",
            output={"content": content},
            metadata={"prompt_logged": False},
            replay_policy="journal_only_replay",
            process_id="proc-1",
            tick=None,
            timestamp=0.0,
            causal_id="causal-1",
        ),
    )


def test_pipeline_llm_service_returns_text() -> None:
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": DummyHandler(),
            "_process_id": "proc-1",
        }
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(prompt="hello"),
        stage="TestStage",
    )

    assert content == "ok"


def test_pipeline_llm_service_missing_handler_records_error() -> None:
    ctx = SimpleNamespace(extra={})

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(prompt="hello"),
        stage="TestStage",
    )

    assert content is None
    error = ctx.extra["errors"][0]

    assert error["stage"] == "TestStage"
    assert error["llm_error"] == "missing_runtime_bindings"


def test_pipeline_llm_service_failure_records_error() -> None:
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": FailingHandler(),
            "_process_id": "proc-1",
        }
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(prompt="hello"),
        stage="TestStage",
    )

    assert content is None
    assert ctx.extra["errors"][0]["llm_error"] == "llm_failed"


def test_pipeline_llm_service_retries_retryable_failure_then_succeeds() -> None:
    handler = RetryThenSuccessHandler()
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": handler,
            "_process_id": "proc-1",
        }
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(prompt="hello"),
        stage="TestStage",
        retry_policy=PipelineRetryPolicy(max_attempts=2),
    )

    event = ctx.extra["llm_retry_events"][0]

    assert content == "ok-after-retry"
    assert handler.calls == 2
    assert ctx.extra["llm_retry_events"][0]["retry"] is True
    assert ctx.extra["llm_retry_events"][1]["success"] is True
    # canonical tick should exist
    assert "tick" in ctx.extra["llm_retry_events"][0]
    assert isinstance(ctx.extra["llm_retry_events"][0]["tick"], int)
    # ticks should be consistent (same tick since no runtime_state)
    assert ctx.extra["llm_retry_events"][0]["tick"] == 0
    assert (
        event.items()
        >= {
            "stage": "TestStage",
            "attempt": 0,
            "success": False,
            "retry": True,
            "error_code": "llm_execution_failed",
            "tick": 0,
            "reason": "retryable",
            "delay_ms": 0,
            "next_attempt": 1,
            "retry_class": "unknown",
        }.items()
    )


def test_pipeline_llm_service_stops_after_retry_limit() -> None:
    handler = AlwaysRetryableFailureHandler()
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": handler,
            "_process_id": "proc-1",
        }
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(prompt="hello"),
        stage="TestStage",
        retry_policy=PipelineRetryPolicy(max_attempts=3),
    )

    assert content is None
    assert handler.calls == 3
    assert ctx.extra["errors"][0]["llm_error"] == "llm_execution_failed"
    assert ctx.extra["llm_retry_events"][-1]["retry"] is False


def test_pipeline_llm_service_does_not_retry_non_retryable_failure() -> None:
    handler = NonRetryableFailureHandler()
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": handler,
            "_process_id": "proc-1",
        }
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(prompt="hello"),
        stage="TestStage",
        retry_policy=PipelineRetryPolicy(max_attempts=3),
    )

    assert content is None
    assert handler.calls == 1
    assert ctx.extra["errors"][0]["llm_error"] == "no_llm_adapter"
    assert ctx.extra["llm_retry_events"][0]["retry"] is False


def test_pipeline_llm_service_stops_when_retry_budget_exhausted() -> None:
    handler = AlwaysRetryableFailureHandler()
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": handler,
            "_process_id": "proc-1",
        }
    )

    content = PipelineLLMService.generate_text(
        ctx,
        request=LLMRequest(prompt="hello"),
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
    assert final_event["budget_remaining"] == 0


def test_llm_service_retries_until_success(mocker):
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": object(),  # mock bypass
            "_process_id": "proc-1",
            "_allow_mock_runtime": True,
        }
    )

    calls = []

    def fake_call(*args, **kwargs):
        if len(calls) < 2:
            calls.append("fail")
            return SyscallResult(success=False, error_detail=_retryable_error())
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
            "_syscall_handler": object(),
            "_process_id": "proc-1",
            "_allow_mock_runtime": True,
        }
    )

    sleep_mock = mocker.patch(
        "arvis.kernel.pipeline.services.pipeline_llm_service.PipelineLLMService._sleep"
    )

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        return_value=SyscallResult(success=False, error_detail=_retryable_error()),
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
            "_syscall_handler": object(),
            "_process_id": "proc-1",
            "_allow_mock_runtime": True,
        }
    )

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        return_value=SyscallResult(success=False, error_detail=_retryable_error()),
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
            "_syscall_handler": object(),
            "_process_id": "proc-1",
            "_allow_mock_runtime": True,
        }
    )

    error = SyscallError(
        code="x",
        message="fail",
        retryable=True,
        metadata={"retry_class": "permanent"},
    )

    mocker.patch(
        _EXECUTE_LLM_SYSCALL,
        return_value=SyscallResult(success=False, error_detail=error),
    )

    result = PipelineLLMService.generate_text(
        ctx,
        request=_request(),
        retry_policy=PipelineRetryPolicy(max_attempts=5),
    )

    assert result is None


def test_pipeline_llm_service_records_structured_output() -> None:
    ctx = SimpleNamespace(
        extra={
            "_syscall_handler": StructuredHandler(),
            "_process_id": "proc-1",
        }
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
