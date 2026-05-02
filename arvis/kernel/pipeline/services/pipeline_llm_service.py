# arvis/kernel/pipeline/services/pipeline_llm_service.py

from __future__ import annotations

import time
from typing import Any, Protocol, cast

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.validation.output_validator import (
    LLMOutputValidator,
    LLMValidationSeverity,
)
from arvis.kernel.pipeline.runtime_bindings import PipelineRuntimeBindings
from arvis.kernel.pipeline.services.pipeline_retry_budget import PipelineRetryBudget
from arvis.kernel.pipeline.services.pipeline_retry_policy import PipelineRetryPolicy
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.errors import SyscallError
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult


class PipelineContextLike(Protocol):
    extra: dict[str, Any]


class SyscallHandlerLike(Protocol):
    def handle(self, syscall: Syscall) -> SyscallResult: ...


class PipelineLLMService:
    @staticmethod
    def generate_text(
        ctx: PipelineContextLike,
        *,
        request: LLMRequest,
        preferred_provider: str | None = None,
        stage: str = "unknown",
        retry_policy: PipelineRetryPolicy | None = None,
        retry_budget: PipelineRetryBudget | None = None,
    ) -> str | None:
        runtime = PipelineLLMService._resolve_runtime_bindings(ctx)

        if runtime is None:
            PipelineLLMService._record_error(
                ctx,
                stage=stage,
                error_code="missing_runtime_bindings",
            )
            return None

        policy = retry_policy or PipelineRetryPolicy(max_attempts=1)
        attempt = 0
        consumed_retries = 0

        while True:
            result = PipelineLLMService._execute_llm_syscall(
                runtime=runtime,
                ctx=ctx,
                request=request,
                preferred_provider=preferred_provider,
            )

            if not result.success:
                # --- SYSCALL FAILURE PATH ---
                error_detail = result.error_detail
                error_code = PipelineLLMService._error_code(result)

                # Normalisation existante (tu peux la garder telle quelle)
                if error_detail is None:
                    error_detail = SyscallError(
                        code=error_code,
                        message="unknown error",
                        retryable=False,
                        metadata={"retry_class": "unknown"},
                    )
                elif error_detail.metadata is None:
                    error_detail = SyscallError(
                        code=error_detail.code,
                        message=error_detail.message,
                        retryable=error_detail.retryable,
                        metadata={"retry_class": "unknown"},
                    )

            else:
                # --- SUCCESS PATH ---
                content = PipelineLLMService._extract_content(
                    ctx,
                    stage=stage,
                    result=result,
                )

                if content is not None:
                    # --- VALIDATION LLM OUTPUT ---
                    require_abstention = "linguistic_act:abstention" in getattr(
                        request, "tags", []
                    )

                    validation = LLMOutputValidator.validate(
                        content,
                        require_abstention=require_abstention,
                    )

                    if request.structured_output is not None:
                        validation = LLMOutputValidator.validate_structured(
                            content,
                            schema=request.structured_output.schema,
                            require_abstention=require_abstention,
                        )

                    if validation.is_valid:
                        if validation.parsed is not None:
                            ctx.extra.setdefault("llm_structured_outputs", {})[
                                stage
                            ] = validation.parsed
                        PipelineLLMService._record_attempt(
                            ctx,
                            stage=stage,
                            attempt=attempt,
                            success=True,
                            retry=False,
                            error_code=None,
                            reason="success",
                            delay_ms=0,
                            next_attempt=attempt,
                            retry_class="unknown",
                        )
                        return content

                    if validation.severity == LLMValidationSeverity.FATAL:
                        error_detail = SyscallError(
                            code="llm_output_fatal",
                            message="Fatal validation failure",
                            retryable=False,
                            metadata={"retry_class": "fatal"},
                        )
                        error_code = "llm_output_fatal"

                    elif validation.severity == LLMValidationSeverity.RETRYABLE:
                        error_detail = SyscallError(
                            code="llm_output_retryable",
                            message="Retryable validation failure",
                            retryable=True,
                            metadata={"retry_class": "validation"},
                        )
                        error_code = "llm_output_retryable"

                        # hint for adaptive retry
                        if request.structured_output is not None:
                            ctx.extra["llm_retry_hint"] = "fix_structured_output"
                        else:
                            ctx.extra["llm_retry_hint"] = "reduce_temperature"

                    elif (
                        validation.severity == LLMValidationSeverity.ABSTENTION_REQUIRED
                    ):
                        return "I don't know."

                    # --- VALIDATION FAILED ---
                    error_code = "llm_output_validation_failed"
                    PipelineLLMService._record_validation_failure(
                        ctx,
                        stage=stage,
                        errors=validation.errors,
                    )

                else:
                    error_detail = SyscallError(
                        code="llm_output_missing",
                        message="No content returned",
                        retryable=False,
                        metadata={"retry_class": "fatal"},
                    )

            decision = policy.decide(
                error=error_detail,
                attempt=attempt,
            )

            # --- Budget integration (clean & safe) ---
            decision_retry = decision.should_retry
            budget_allowed = None
            budget_remaining = None
            budget_reason = None

            if decision.should_retry and retry_budget is not None:
                budget_decision = retry_budget.decide(
                    consumed_retries=consumed_retries,
                )

                budget_allowed = budget_decision.allowed
                budget_remaining = budget_decision.remaining
                budget_reason = budget_decision.reason

                decision_retry = decision.should_retry and budget_decision.allowed

            # --- Record attempt ---
            PipelineLLMService._record_attempt(
                ctx,
                stage=stage,
                attempt=attempt,
                success=False,
                retry=decision_retry,
                error_code=error_code,
                reason=decision.reason,
                delay_ms=decision.delay_ms,
                next_attempt=decision.next_attempt,
                retry_class=decision.retry_class,
                budget_allowed=budget_allowed,
                budget_remaining=budget_remaining,
                budget_reason=budget_reason,
            )

            # --- Exit condition ---
            if not decision_retry:
                PipelineLLMService._record_error(
                    ctx,
                    stage=stage,
                    error_code=error_code,
                    error_detail=error_detail,
                )
                return None

            # --- Apply delay ---
            if decision.delay_ms > 0:
                PipelineLLMService._sleep(decision.delay_ms)

            consumed_retries += 1
            attempt = decision.next_attempt

    @staticmethod
    def _execute_llm_syscall(
        *,
        runtime: PipelineRuntimeBindings,
        ctx: PipelineContextLike,
        request: LLMRequest,
        preferred_provider: str | None,
    ) -> SyscallResult:
        args: dict[str, Any] = {
            "ctx": ctx,
            "request": request,
            "process_id": runtime.process_id,
        }

        if preferred_provider is not None:
            args["preferred_provider"] = preferred_provider

        return runtime.syscall_handler.handle(
            Syscall(
                name="llm.generate",
                args=args,
            )
        )

    @staticmethod
    def _extract_content(
        ctx: PipelineContextLike,
        *,
        stage: str,
        result: SyscallResult,
    ) -> str | None:
        artifact = result.result

        if not isinstance(artifact, ExecutionArtifact):
            PipelineLLMService._record_error(
                ctx,
                stage=stage,
                error_code="invalid_llm_artifact",
            )
            return None

        output = artifact.output

        if not isinstance(output, dict):
            PipelineLLMService._record_error(
                ctx,
                stage=stage,
                error_code="invalid_llm_artifact_output",
            )
            return None

        content = output.get("content")

        if not isinstance(content, str):
            PipelineLLMService._record_error(
                ctx,
                stage=stage,
                error_code="missing_llm_content",
            )
            return None

        return content

    @staticmethod
    def _error_code(result: SyscallResult) -> str:
        if result.error_detail is not None:
            return result.error_detail.code

        # Legacy fallback normalization (strip message if present)
        if result.error is not None:
            return result.error.split(":", 1)[0]

        return "unknown_llm_syscall_error"

    @staticmethod
    def _record_error(
        ctx: PipelineContextLike,
        *,
        stage: str,
        error_code: str,
        error_detail: SyscallError | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "stage": stage,
            "llm_error": error_code,
        }

        if error_detail is not None:
            entry["llm_error_detail"] = error_detail.to_dict()

        ctx.extra.setdefault("errors", []).append(entry)

    @staticmethod
    def _record_attempt(
        ctx: PipelineContextLike,
        *,
        stage: str,
        attempt: int,
        success: bool,
        retry: bool,
        error_code: str | None,
        reason: str,
        delay_ms: int,
        next_attempt: int,
        retry_class: str,
        budget_allowed: bool | None = None,
        budget_remaining: int | None = None,
        budget_reason: str | None = None,
    ) -> None:
        tick = PipelineLLMService._get_tick(ctx)

        ctx.extra.setdefault("llm_retry_events", []).append(
            {
                "stage": stage,
                "attempt": attempt,
                "success": success,
                "retry": retry,
                "error_code": error_code,
                # Production observability
                # Canonical timeline-aligned time
                "tick": tick,
                "reason": reason,
                "delay_ms": delay_ms,
                "next_attempt": next_attempt,
                "retry_class": retry_class,
                "budget_allowed": budget_allowed,
                "budget_remaining": budget_remaining,
                "budget_reason": budget_reason,
            }
        )

    @staticmethod
    def _get_tick(ctx: PipelineContextLike) -> int:
        runtime = ctx.extra.get("_runtime")

        if runtime is not None and hasattr(runtime, "syscall_handler"):
            handler = runtime.syscall_handler
            runtime_state = getattr(handler, "runtime_state", None)

            if runtime_state is not None:
                return int(runtime_state.scheduler_state.tick_count)

        return 0

    @staticmethod
    def _resolve_runtime_bindings(
        ctx: PipelineContextLike,
    ) -> PipelineRuntimeBindings | None:
        runtime = ctx.extra.get("_runtime")

        if isinstance(runtime, PipelineRuntimeBindings):
            return runtime

        handler_obj = ctx.extra.get("_syscall_handler")
        process_id_obj = ctx.extra.get("_process_id")

        if handler_obj is None or not hasattr(handler_obj, "handle"):
            # allow mocked syscall path (tests / injection)
            if "_allow_mock_runtime" in ctx.extra:
                if not isinstance(process_id_obj, str):
                    return None
                return PipelineRuntimeBindings(
                    syscall_handler=cast(SyscallHandlerLike, handler_obj),
                    process_id=process_id_obj,
                )
            return None

        if not isinstance(process_id_obj, str):
            return None

        return PipelineRuntimeBindings(
            syscall_handler=cast(SyscallHandlerLike, handler_obj),
            process_id=process_id_obj,
        )

    @staticmethod
    def _sleep(delay_ms: int) -> None:
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

    @staticmethod
    def _record_validation_failure(
        ctx: PipelineContextLike,
        *,
        stage: str,
        errors: list[Any],
    ) -> None:
        ctx.extra.setdefault("llm_validation_errors", []).append(
            {
                "stage": stage,
                "errors": [{"code": e.code, "message": e.message} for e in errors],
            }
        )
