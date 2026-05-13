# arvis/kernel_core/syscalls/syscalls/llm_syscalls.py

from __future__ import annotations

from typing import Any, Protocol

from arvis.adapters.llm.contracts.execution_result import LLMExecutionResult
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.tracing import LLMTrace, serialize_response, serialize_trace
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.errors import SyscallError
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall


class LLMAdapterLike(Protocol):
    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMExecutionResult: ...


class ServiceRegistryLike(Protocol):
    llm_adapter: LLMAdapterLike | None


class SyscallHandlerLike(Protocol):
    services: ServiceRegistryLike
    runtime_state: Any | None


def _compute_artifact_timestamp(
    handler: SyscallHandlerLike,
    kwargs: dict[str, Any],
) -> float:
    tick = kwargs.get("tick")
    if tick is not None:
        return float(tick)

    runtime_state = getattr(handler, "runtime_state", None)
    if runtime_state is not None:
        return float(runtime_state.scheduler_state.tick_count)

    return 0.0


@register_syscall("llm.generate")
def llm_generate(
    handler: SyscallHandlerLike,
    request: LLMRequest,
    ctx: Any | None = None,
    preferred_provider: str | None = None,
    **kwargs: Any,
) -> SyscallResult:
    adapter = handler.services.llm_adapter

    if adapter is None:
        return SyscallResult.failure(
            SyscallError(
                code="no_llm_adapter",
                message="LLM adapter not configured",
                retryable=False,
            )
        )

    try:
        execution = adapter.generate(
            request=request,
            preferred_provider=preferred_provider,
        )
    except Exception as exc:
        retry_class = "transient"

        return SyscallResult.failure(
            SyscallError(
                code="llm_execution_failed",
                message=str(exc),
                retryable=True,
                metadata={
                    "exception": type(exc).__name__,
                    "retry_class": retry_class,
                },
            )
        )

    response = execution.response

    if response is None:
        return SyscallResult.failure(
            SyscallError(
                code="llm_missing_response",
                message="LLM execution returned no response",
                retryable=False,
            )
        )

    if hasattr(response, "response"):
        response = response.response

    if not isinstance(response, LLMResponse):
        raise TypeError("llm adapter returned invalid response type")

    trace_id = response.trace_id or str(kwargs.get("causal_id") or "llm.generate")

    trace = LLMTrace.from_response(
        trace_id=trace_id,
        syscall="llm.generate",
        request=request,
        response=response,
        preferred_provider=preferred_provider,
    )

    artifact_metadata = serialize_trace(trace)
    artifact_metadata["seq"] = getattr(handler, "_local_counter", 0)
    artifact_metadata["prompt_logged"] = False

    metadata = getattr(response, "metadata", None)

    if isinstance(metadata, dict):
        llm_observation = metadata.get("llm_observation")
        if isinstance(llm_observation, dict):
            artifact_metadata["llm_observation"] = llm_observation

        artifact_metadata["llm_execution"] = {
            "status": execution.status.value,
            "retry_count": execution.retry_count,
            "fallback_used": execution.fallback_used,
            "degraded": execution.degraded,
            "require_confirmation": execution.require_confirmation,
        }

        llm_evaluation = metadata.get("llm_evaluation")
        if isinstance(llm_observation, dict):
            artifact_metadata["llm_evaluation"] = llm_evaluation

    artifact = ExecutionArtifact(
        artifact_type="llm_generation",
        syscall="llm.generate",
        status="success",
        output=serialize_response(response),
        metadata=artifact_metadata,
        replay_policy="journal_only_replay",
        process_id=kwargs.get("process_id"),
        tick=kwargs.get("tick"),
        timestamp=_compute_artifact_timestamp(handler, kwargs),
        causal_id=kwargs.get("causal_id"),
    )

    return SyscallResult(
        success=True,
        result=artifact,
    )
