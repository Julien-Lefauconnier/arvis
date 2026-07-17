# arvis/kernel_core/syscalls/syscall_handler.py

from __future__ import annotations

import inspect
from typing import Any, Protocol

from arvis.errors import ErrorOrigin
from arvis.errors.base import ArvisSecurityError
from arvis.errors.codes import ErrorCode
from arvis.errors.manager import ErrorManager
from arvis.errors.messages import safe_exception_message
from arvis.errors.normalization import normalize_error
from arvis.errors.syscall import SyscallExecutionError, SyscallValidationError
from arvis.errors.types import ErrorPayload
from arvis.kernel_core.access.identity import principal_from_context
from arvis.kernel_core.access.policy import (
    ACCESS_DENIED_REASON_CODE,
    AuthorizationPolicy,
    OwnerScopedAuthorization,
)
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.engagement import effect_engagement_digest
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    SyscallFn,
    get_descriptor,
    get_syscall,
)


class RuntimeStateLike(Protocol):
    scheduler_state: Any

    def append_event(self, name: str, payload: dict[str, Any]) -> None: ...


class PipelineContextLike(Protocol):
    extra: dict[str, Any]


def _execution_state_from_ctx(ctx: Any) -> Any | None:
    execution = getattr(ctx, "execution", None)
    runtime = getattr(execution, "execution_state", None)
    if runtime is not None:
        return runtime

    return getattr(ctx, "execution_state", None)


class SyscallHandler:
    def __init__(
        self,
        runtime_state: RuntimeStateLike | None,
        scheduler: Any,
        services: KernelServiceRegistry | None = None,
    ) -> None:
        self.runtime_state = runtime_state
        self.scheduler = scheduler
        self.services = services or KernelServiceRegistry()
        self._local_counter: int = 0
        self._last_tick: int = -1

        # Backward-compatible convenience aliases
        self.tool_executor = self.services.tool_executor
        self.vfs_service = self.services.vfs_service
        self.zip_ingest_service = self.services.zip_ingest_service
        self.authorization_service: AuthorizationPolicy = (
            self.services.authorization_service or OwnerScopedAuthorization()
        )

    def handle(self, syscall: Syscall) -> SyscallResult:
        ctx: PipelineContextLike | None = syscall.args.get("ctx")
        fn: SyscallFn | None = get_syscall(syscall.name)
        started_tick = self._get_tick()

        if started_tick != self._last_tick:
            self._local_counter = 0
            self._last_tick = started_tick

        self._local_counter += 1

        if fn is None:
            missing_result = self._failure_from_error(
                ctx,
                SyscallValidationError(
                    f"Unknown syscall: {syscall.name}",
                    code=ErrorCode.UNKNOWN_SYSCALL,
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={"syscall": syscall.name},
                ),
            )
            self._safe_journal(ctx, syscall, missing_result, started_tick)
            return missing_result

        sig = inspect.signature(fn)
        try:
            sig.bind(self, **syscall.args)
        except TypeError as exc:
            error_result = self._failure_from_error(
                ctx,
                SyscallValidationError(
                    safe_exception_message(exc, fallback="invalid syscall arguments"),
                    code=ErrorCode.INVALID_SYSCALL_ARGS,
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "exception_type": type(exc).__name__,
                    },
                    cause=None,
                ),
            )
            self._safe_journal(ctx, syscall, error_result, started_tick)
            return error_result

        descriptor = get_descriptor(syscall.name)
        authorization_reason_code: str | None = None
        if descriptor is not None and descriptor.access is not None:
            # P1-13-a6: a failing resolver or policy never leaks a raw
            # exception through the syscall boundary. The refusal is
            # normalized (stable reason code, journaled) and stays
            # fail-closed.
            try:
                access_ctx = descriptor.access(syscall.args, self.services)
                verdict = self.authorization_service.decide(access_ctx)
            except Exception as exc:
                machinery_failure = self._failure_from_error(
                    ctx,
                    ArvisSecurityError(
                        "authorization machinery failure; the syscall "
                        "is refused (fail-closed)",
                        origin=ErrorOrigin(
                            component="SyscallHandler",
                            subsystem="kernel.syscall",
                            syscall=syscall.name,
                        ),
                        details={
                            "syscall": syscall.name,
                            "reason_code": "authorization_failure",
                            "exception_type": type(exc).__name__,
                        },
                    ),
                )
                self._safe_journal(ctx, syscall, machinery_failure, started_tick)
                return machinery_failure
            authorization_reason_code = verdict.reason_code
            if not verdict.allowed:
                denied_result = self._failure_from_error(
                    ctx,
                    ArvisSecurityError(
                        "access denied",
                        origin=ErrorOrigin(
                            component="SyscallHandler",
                            subsystem="kernel.syscall",
                            syscall=syscall.name,
                        ),
                        details={
                            "syscall": syscall.name,
                            "reason_code": verdict.reason_code
                            or ACCESS_DENIED_REASON_CODE,
                        },
                    ),
                )
                self._safe_journal(ctx, syscall, denied_result, started_tick)
                return denied_result

        causal_id = self._build_syscall_id(
            syscall,
            started_tick,
            self._local_counter,
        )

        # F-008-a5 (outbox): the intent precedes the effect. For any
        # EFFECT syscall a durable intent entry is recorded BEFORE the
        # call; an intent that cannot be recorded refuses the syscall
        # (fail-closed). An intent without a paired artifact afterwards
        # signals a crash during the effect: the uncertainty is bounded
        # and visible, never silent.
        if descriptor is not None and descriptor.effect is SyscallEffect.EFFECT:
            intent_refusal = self._record_intent(
                ctx,
                syscall,
                causal_id,
                started_tick,
                authorization_reason_code=authorization_reason_code,
            )
            if intent_refusal is not None:
                self._safe_journal(ctx, syscall, intent_refusal, started_tick)
                return intent_refusal

        try:
            syscall_result = fn(
                self,
                **{
                    **syscall.args,
                    "causal_id": causal_id,
                },
            )
        except Exception as exc:
            error_result = self._failure_from_exception(
                ctx,
                exc,
                syscall_name=syscall.name,
            )
            self._safe_journal(ctx, syscall, error_result, started_tick)
            return error_result

        if not isinstance(syscall_result, SyscallResult):
            syscall_result = self._failure_from_error(
                ctx,
                SyscallValidationError(
                    f"Invalid syscall return type: {type(syscall_result).__name__}",
                    code=ErrorCode.INVALID_SYSCALL_RETURN_TYPE,
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "return_type": type(syscall_result).__name__,
                    },
                ),
            )

        self._safe_journal(ctx, syscall, syscall_result, started_tick)
        return syscall_result

    def _record_intent(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        causal_id: str,
        started_tick: int,
        *,
        authorization_reason_code: str | None = None,
    ) -> SyscallResult | None:
        """Record a durable audit intent before an effect syscall.

        The entry carries structural metadata only (syscall name, causal
        id, tick, process id): no payload material enters the journal
        (ZK; the redacted payload hash is a lot-6 enrichment once the
        redaction policy exists). The entry is appended to the ordered
        ``ctx.extra["syscall_intents"]`` channel (paired with the result
        journal through the shared causal id), emitted as a
        ``syscall_intent`` runtime event, and handed to the host
        ``audit_intent_sink`` when configured. ANY failure to record
        refuses the syscall: an intent that cannot be made durable must
        not be followed by its effect (fail-closed).
        """
        intent: dict[str, Any] = {
            "kind": "syscall_intent",
            "syscall": syscall.name,
            "causal_id": causal_id,
            "tick": started_tick,
            "process_id": syscall.args.get("process_id") or "none",
        }
        try:
            # P0-3-a6: engage the exact parameters of the effect BEFORE
            # it runs. The digest binds the materialized redacted
            # arguments, the principal, the tenant, the turn owner and
            # the authorization outcome; only the hash enters the
            # journal, never the parameters themselves (ZKCS).
            args_ctx = syscall.args.get("ctx")
            principal = principal_from_context(args_ctx)
            intent["commitment_sha256"] = effect_engagement_digest(
                syscall_name=syscall.name,
                args=dict(syscall.args),
                principal_user_id=(
                    principal.user_id if principal is not None else None
                ),
                principal_organization_id=(
                    principal.organization_id if principal is not None else None
                ),
                turn_user_id=getattr(args_ctx, "user_id", None),
                authorization_reason_code=authorization_reason_code,
            )
            if ctx is not None:
                intents = ctx.extra.setdefault("syscall_intents", [])
                if isinstance(intents, list):
                    intents.append(intent)
                execution_state = _execution_state_from_ctx(ctx)
                state_intents = getattr(execution_state, "syscall_intents", None)
                if isinstance(state_intents, list):
                    state_intents.append(intent)
            if self.runtime_state is not None:
                self.runtime_state.append_event(
                    "syscall_intent",
                    {
                        "process_id": intent["process_id"],
                        "syscall_id": causal_id,
                        "syscall_name": syscall.name,
                        "tick": started_tick,
                        "causal_id": causal_id,
                    },
                )
            sink = self.services.audit_intent_sink
            if sink is not None:
                # The host receives a copy: mutating it never rewrites
                # the journaled entry.
                sink(dict(intent))
        except Exception as exc:
            return self._failure_from_error(
                ctx,
                ArvisSecurityError(
                    "audit intent could not be recorded before the "
                    "effect; the syscall is refused (fail-closed)",
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "audit_intent_failed",
                        "exception_type": type(exc).__name__,
                    },
                ),
            )
        return None

    def _safe_journal(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        result: SyscallResult,
        started_tick: int,
    ) -> None:
        try:
            self._journal(ctx, syscall, result, started_tick)
        except Exception as exc:
            if ctx is not None:
                ErrorManager.attach(
                    ctx,
                    SyscallExecutionError(
                        "Syscall journaling failure",
                        origin=ErrorOrigin(
                            component="SyscallHandler",
                            subsystem="kernel.syscall",
                            syscall=syscall.name,
                        ),
                        details={
                            "syscall": syscall.name,
                            "component": "SyscallHandler._journal",
                            "exception_type": type(exc).__name__,
                            "recovery": "journal_failure_suppressed",
                        },
                        cause=normalize_error(exc).cause,
                    ),
                )

    def _journal(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        result: SyscallResult,
        started_tick: int,
    ) -> None:
        if ctx is None:
            return

        end_tick = self._get_tick()
        elapsed_ticks = self._compute_elapsed_ticks(started_tick, end_tick)
        execution_state = _execution_state_from_ctx(ctx)

        if execution_state is not None:
            results = execution_state.syscall_results
            ctx.extra["syscall_results"] = results
        else:
            results = ctx.extra.setdefault("syscall_results", [])

        syscall_id = self._build_syscall_id(
            syscall,
            started_tick,
            self._local_counter,
        )

        entry: dict[str, Any] = {
            "syscall_id": syscall_id,
            "causal_id": syscall_id,
            "syscall": syscall.name,
            "success": result.success,
            "elapsed_ticks": elapsed_ticks,
            "replay_policy": self._default_replay_policy(syscall.name),
            "tick": end_tick,
            "tick_start": started_tick,
            "tick_end": end_tick,
        }

        process_id = syscall.args.get("process_id")
        tick = syscall.args.get("tick")
        retry_attempt = syscall.args.get("retry_attempt")
        retry_chain_id = syscall.args.get("retry_chain_id")
        retry_parent_syscall_id = syscall.args.get("retry_parent_syscall_id")

        if process_id is not None:
            entry["process_id"] = process_id

        if tick is not None:
            entry["tick"] = tick

        if retry_attempt is not None:
            entry["retry_attempt"] = int(retry_attempt)

        if retry_chain_id is not None:
            entry["retry_chain_id"] = str(retry_chain_id)

        if retry_parent_syscall_id is not None:
            entry["retry_parent_syscall_id"] = str(retry_parent_syscall_id)

        if isinstance(result.result, ExecutionArtifact):
            entry["artifact"] = result.result.to_dict()
            entry["artifact_timestamp"] = result.result.timestamp
            entry["artifact"]["causal_id"] = entry["syscall_id"]
            if retry_attempt is not None:
                entry["artifact"]["metadata"]["retry_attempt"] = int(retry_attempt)
            if retry_chain_id is not None:
                entry["artifact"]["metadata"]["retry_chain_id"] = str(retry_chain_id)
            if retry_parent_syscall_id is not None:
                entry["artifact"]["metadata"]["retry_parent_syscall_id"] = str(
                    retry_parent_syscall_id
                )

        # -----------------------------------------
        # DEFAULT RESULT LOGGING
        # -----------------------------------------
        if result.result is not None:
            entry["result"] = result.result

        if result.error is not None:
            entry["error"] = result.error.to_dict()

        if isinstance(results, list):
            results.append(entry)

        if execution_state is not None:
            execution_state.metadata["last_syscall_result"] = entry

        ctx.extra["last_syscall_result"] = entry

        self._append_syscall_runtime_event(entry)

    def _default_replay_policy(self, syscall_name: str) -> str:
        if syscall_name == "tool.execute":
            return "journal_only_replay"

        if syscall_name.startswith("llm."):
            return "journal_only_replay"

        if syscall_name.startswith("vfs.") and syscall_name not in {
            "vfs.list",
            "vfs.tree",
            "vfs.zip.analyze",
        }:
            return "journal_only_replay"

        if syscall_name in {"vfs.list", "vfs.tree", "vfs.zip.analyze"}:
            return "recompute"

        return "unknown"

    def _get_tick(self) -> int:
        if self.runtime_state is None:
            return 0
        return int(self.runtime_state.scheduler_state.tick_count)

    def _compute_elapsed_ticks(self, started_tick: int, end_tick: int) -> float:
        return float(end_tick - started_tick)

    def _build_syscall_id(
        self,
        syscall: Syscall,
        tick: int,
        seq: int,
    ) -> str:
        process_id = syscall.args.get("process_id", "none")
        return f"syscall:{syscall.name}:{process_id}:{tick}:{seq}"

    def _append_syscall_runtime_event(self, entry: dict[str, Any]) -> None:
        if self.runtime_state is None:
            return

        event_type = "syscall_succeeded" if entry.get("success") else "syscall_failed"

        payload = {
            "process_id": entry.get("process_id", "none"),
            "syscall_id": entry["syscall_id"],
            "syscall_name": entry["syscall"],
            "tick": entry.get("tick", 0),
            "replay_policy": entry.get("replay_policy"),
            "causal_id": entry["syscall_id"],
        }

        artifact = entry.get("artifact")
        if isinstance(artifact, dict):
            payload["artifact_id"] = artifact.get("id")

        self.runtime_state.append_event(event_type, payload)

    def _failure_from_exception(
        self,
        ctx: PipelineContextLike | None,
        exc: Exception,
        *,
        syscall_name: str,
    ) -> SyscallResult:
        normalized = normalize_error(exc)

        arvis_error = SyscallExecutionError(
            normalized.message,
            origin=ErrorOrigin(
                component="SyscallHandler",
                subsystem="kernel.syscall",
                syscall=syscall_name,
            ),
            details={
                "syscall": syscall_name,
                "exception_type": type(exc).__name__,
            },
            cause=normalized.cause,
        )
        return self._failure_from_error(ctx, arvis_error)

    def _failure_from_error(
        self,
        ctx: PipelineContextLike | None,
        error: Exception,
    ) -> SyscallResult:
        arvis_error = normalize_error(error)

        if ctx is not None:
            ErrorManager.attach(ctx, arvis_error)

        return SyscallResult.failure(arvis_error)

    def _attach_or_normalize(
        self,
        ctx: PipelineContextLike | None,
        error: Exception,
    ) -> ErrorPayload:
        if ctx is None:
            return normalize_error(error).to_dict()

        return ErrorManager.attach(ctx, error)
