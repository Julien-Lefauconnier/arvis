# tests/kernel_core/test_llm_syscall.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler


def make_ctx():
    return SimpleNamespace(extra={})


class DummyLLMAdapter:
    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            content=f"answer:{request.prompt}",
            provider=preferred_provider or "mock",
            model="mock-model",
            usage=LLMUsage(
                prompt_tokens=2,
                completion_tokens=3,
                total_tokens=5,
            ),
            metadata={"ok": True},
        )


class FailingLLMAdapter:
    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMResponse:
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
    assert result.error_detail is not None
    assert result.error_detail.code == "no_llm_adapter"


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
    assert result.error_detail is not None
    assert result.error_detail.code == "llm_execution_failed"
    assert result.error_detail.retryable is True
    assert result.error_detail.metadata == {
        "exception": "TimeoutError",
        "retry_class": "transient",
    }
