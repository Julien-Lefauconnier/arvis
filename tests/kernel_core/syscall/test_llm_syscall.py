# tests/kernel_core/syscall/test_llm_syscall.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.llm.contracts.execution_result import (
    LLMExecutionResult,
    LLMExecutionStatus,
)
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage
from arvis.kernel_core.syscalls.service_registry import (
    KernelServiceRegistry,
)
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import (
    SyscallHandler,
)


def make_ctx():
    return SimpleNamespace(extra={})


class DummyLLMAdapter:
    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMExecutionResult:
        response = LLMResponse(
            content=f"answer:{request.prompt}",
            provider=preferred_provider or "mock",
            usage=LLMUsage(
                prompt_tokens=2,
                completion_tokens=3,
                total_tokens=5,
            ),
            metadata={},
        )

        return LLMExecutionResult(
            status=LLMExecutionStatus.SUCCESS,
            response=response,
            retry_count=0,
            fallback_used=False,
            provider_attempts=(),
            evaluation={},
            observation={},
            error=None,
            degraded=False,
            replay_safe=False,
            require_confirmation=False,
        )


class FailingLLMAdapter:
    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMExecutionResult:
        raise TimeoutError("provider timeout")


def test_llm_generate_syscall_success() -> None:
    ctx = make_ctx()

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            llm_adapter=DummyLLMAdapter(),
        ),
    )

    result = handler.handle(
        Syscall(
            name="llm.generate",
            args={
                "ctx": ctx,
                "request": LLMRequest(prompt="hello"),
                "preferred_provider": "mock",
            },
        )
    )

    assert result.success is True
    assert result.result is not None

    artifact = result.result

    assert artifact.artifact_type == "llm_generation"
    assert artifact.output["content"] == "answer:hello"
    assert artifact.output["provider"] == "mock"
    assert artifact.output["usage"]["total_tokens"] == 5

    entry = ctx.extra["syscall_results"][0]

    assert entry["syscall"] == "llm.generate"
    assert entry["success"] is True

    assert entry["artifact"]["metadata"]["prompt_logged"] is False


def test_llm_generate_syscall_missing_adapter() -> None:
    ctx = make_ctx()

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    result = handler.handle(
        Syscall(
            name="llm.generate",
            args={
                "ctx": ctx,
                "request": LLMRequest(prompt="hello"),
            },
        )
    )

    assert result.success is False
    assert result.error is not None

    assert result.error.code == "no_llm_adapter"
    assert result.error.retryable is False


def test_llm_generate_syscall_failure_has_retry_class() -> None:
    ctx = make_ctx()

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            llm_adapter=FailingLLMAdapter(),
        ),
    )

    result = handler.handle(
        Syscall(
            name="llm.generate",
            args={
                "ctx": ctx,
                "request": LLMRequest(prompt="hello"),
            },
        )
    )

    assert result.success is False
    assert result.error is not None

    error = result.error

    assert error.code == "llm_execution_failed"
    assert error.retryable is True
    assert error.domain == "llm"
    assert error.details["classification"] == "external"

    assert error.details == {
        "exception_type": "TimeoutError",
        "classification": "external",
        "retry_class": "transient",
    }
