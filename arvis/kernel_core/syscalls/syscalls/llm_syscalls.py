# arvis/kernel_core/syscalls/syscalls/llm_syscalls.py

from __future__ import annotations

from typing import Any, Protocol

from arvis.adapters.llm.contracts.execution_result import LLMExecutionResult
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.tracing import LLMTrace, serialize_response, serialize_trace
from arvis.errors.base import (
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.errors.manager import ErrorManager
from arvis.errors.provenance import ErrorOrigin
from arvis.kernel_core.access.resolvers import turn_owner_resolver
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    register_syscall,
)


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


@register_syscall(
    "llm.generate",
    effect=SyscallEffect.EFFECT,
    triggers_external=True,
    summary="Invoke the language model to realize text.",
    access=turn_owner_resolver(SyscallEffect.EFFECT, "llm.generate"),
)
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
            ArvisRuntimeError(
                "LLM adapter not configured",
                code="no_llm_adapter",
                domain=ErrorDomain.LLM,
                details={
                    "syscall": "llm.generate",
                },
            )
        )

    try:
        execution = adapter.generate(
            request=request,
            preferred_provider=preferred_provider,
        )
    except Exception as exc:
        error = ErrorManager.normalize_for_boundary(
            exc,
            boundary="external",
            code="llm_execution_failed",
            domain=ErrorDomain.LLM,
            origin=ErrorOrigin(
                component="llm.generate",
                subsystem="kernel.syscall",
                syscall="llm.generate",
            ),
            details={
                "retry_class": "transient",
            },
        )

        return SyscallResult.failure(error)

    response = execution.response

    if response is None:
        return SyscallResult.failure(
            ArvisRuntimeError(
                "LLM execution returned no response",
                code="llm_missing_response",
                domain=ErrorDomain.LLM,
                details={
                    "syscall": "llm.generate",
                },
            )
        )

    if hasattr(response, "response"):
        response = response.response

    if not isinstance(response, LLMResponse):
        return SyscallResult.failure(
            ArvisRuntimeError(
                "llm adapter returned invalid response type",
                code="llm_invalid_response_type",
                domain=ErrorDomain.LLM,
                details={
                    "expected_type": "LLMResponse",
                    "received_type": type(response).__name__,
                },
            )
        )

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
        if isinstance(llm_evaluation, dict):
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
