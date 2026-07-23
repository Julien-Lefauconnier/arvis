# arvis/kernel_core/syscalls/syscall_handler.py

from __future__ import annotations

import inspect
from typing import Any, Protocol, cast

from arvis.errors import ErrorOrigin
from arvis.errors.base import ArvisSecurityError
from arvis.errors.codes import ErrorCode
from arvis.errors.manager import ErrorManager
from arvis.errors.messages import safe_exception_message
from arvis.errors.normalization import normalize_error
from arvis.errors.syscall import SyscallExecutionError, SyscallValidationError
from arvis.errors.types import ErrorPayload
from arvis.kernel_core.access.identity import (
    authenticated_principal_from_context,
    principal_from_context,
)
from arvis.kernel_core.access.models import KERNEL_OWNER_ID, KERNEL_PRINCIPAL
from arvis.kernel_core.access.policy import (
    ACCESS_DENIED_REASON_CODE,
    AuthorizationPolicy,
    OwnerScopedAuthorization,
)
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.engagement import effect_engagement_digest
from arvis.kernel_core.syscalls.intent_outbox import (
    IntentOutboxRefusal,
    IntentOutboxService,
    RecordedIntent,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    SyscallFn,
    get_descriptor,
    get_syscall,
)
from arvis.tools.authorized_invocation import UnauthorizedExecutionError
from arvis.tools.effect_context import build_authorized_effect_context
from arvis.tools.manager import (
    ToolAuthorizationOutcome,
    ToolManager,
    _ToolEffectBoundary,
)
from arvis.tools.runtime.runtime_bindings import resolve_process_id, resolve_run_id


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
        self._tool_effect_boundary: _ToolEffectBoundary | None = None
        configured_manager = self.services.tool_manager
        if isinstance(configured_manager, ToolManager):
            self._tool_effect_boundary = configured_manager._claim_effect_boundary()
        self._local_counter: int = 0
        self._last_tick: int = -1
        # Campaign 6 (Lot 2, closes a8 section 9): the engagement digest
        # of each recorded intent, keyed by causal id, popped when the
        # paired result is journaled so the result carries the EXACT
        # commitment of its intent (single use per causal id). Bounded
        # by the intents of the current run; runtime lifecycle bounding
        # is a tracked later chantier (a8 section 22).
        self._pending_intent_commitments: dict[str, str] = {}
        # Campaign 6 (Lot 5), hardened by campaign 7 (Lot 7): identity
        # of the current run, set by the runtime at run entry. When set,
        # the COMPLETE run id prefixes every causal id (global uniqueness
        # across runs in a shared sink) and is journaled on every intent and
        # host-side reconciliation. It is ENVELOPE identity: stripped
        # from the hashed material like the causal ids it prefixes, so
        # the commitment stays deterministic; the run <-> commitment
        # anchoring belongs to the durable sink (receipt, Lot 6). None
        # outside a runtime-entered run (direct handler tests keep the
        # legacy id shape).
        self._current_run_id: str | None = None
        self._intent_outbox = IntentOutboxService(
            services=self.services,
            runtime_state=runtime_state,
            pending_intent_commitments=self._pending_intent_commitments,
        )

        # Backward-compatible convenience aliases
        self.tool_executor = self.services.tool_executor
        self.vfs_service = self.services.vfs_service
        self.zip_ingest_service = self.services.zip_ingest_service
        self.authorization_service: AuthorizationPolicy = (
            self.services.authorization_service or OwnerScopedAuthorization()
        )

    def begin_run(self, run_id: str) -> None:
        """Mark the entry of a run (campaign 6, Lot 5).

        Called by the runtime with a fresh unguessable run id before
        any syscall of the run. Also clears the pending intent
        commitment map: a run boundary never leaks pairing state into
        the next run.
        """
        self._current_run_id = run_id
        self._pending_intent_commitments.clear()

    def handle(self, syscall: Syscall) -> SyscallResult:
        """Coordinate admission, outbox activation, dispatch and journaling."""
        ctx, fn, started_tick, preparation_failure = self._prepare_registered_call(
            syscall
        )
        if preparation_failure is not None:
            return preparation_failure
        resolution_failure = self._refuse_missing_registered_function(
            ctx, syscall, fn, started_tick
        )
        if resolution_failure is not None:
            return resolution_failure
        fn = cast(SyscallFn, fn)

        descriptor = get_descriptor(syscall.name)
        authorization_reason_code, access_failure = self._authorize_registered_call(
            ctx,
            syscall,
            descriptor,
            started_tick,
        )
        if access_failure is not None:
            self._abort_presented_tool_authorization(syscall)
            return access_failure

        tool_authorization: ToolAuthorizationOutcome | None = None
        if syscall.name == "tool.execute":
            tool_authorization, authorization_failure = (
                self._validate_tool_authorization_outcome(ctx, syscall)
            )
            if authorization_failure is not None:
                self._safe_journal(ctx, syscall, authorization_failure, started_tick)
                return authorization_failure

        is_effect = descriptor is not None and descriptor.effect is SyscallEffect.EFFECT
        identity_failure = self._validate_effect_identity(
            ctx,
            syscall,
            started_tick,
            is_effect=is_effect,
            tool_authorization=tool_authorization,
        )
        if identity_failure is not None:
            return identity_failure

        effect_context_failure = self._validate_tool_effect_context(
            ctx,
            syscall,
            started_tick,
            tool_authorization,
        )
        if effect_context_failure is not None:
            return effect_context_failure

        causal_id = self._build_syscall_id(
            syscall,
            started_tick,
            self._local_counter,
        )
        if is_effect:
            transaction_failure = self._open_effect_transaction(
                ctx,
                syscall,
                causal_id,
                started_tick,
                authorization_reason_code=authorization_reason_code,
                tool_authorization=tool_authorization,
            )
            if transaction_failure is not None:
                return transaction_failure

        return self._invoke_and_journal(
            ctx=ctx,
            syscall=syscall,
            fn=fn,
            causal_id=causal_id,
            started_tick=started_tick,
            is_effect=is_effect,
            tool_authorization=tool_authorization,
        )

    def _prepare_registered_call(
        self,
        syscall: Syscall,
    ) -> tuple[
        PipelineContextLike | None,
        SyscallFn | None,
        int,
        SyscallResult | None,
    ]:
        ctx: PipelineContextLike | None = syscall.args.get("ctx")
        fn = get_syscall(syscall.name)
        started_tick = self._get_tick()
        if started_tick != self._last_tick:
            self._local_counter = 0
            self._last_tick = started_tick
        self._local_counter += 1

        if fn is None:
            failure = self._failure_from_error(
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
            self._safe_journal(ctx, syscall, failure, started_tick)
            return ctx, None, started_tick, failure

        try:
            inspect.signature(fn).bind(self, **syscall.args)
        except TypeError as exc:
            failure = self._failure_from_error(
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
            self._safe_journal(ctx, syscall, failure, started_tick)
            return ctx, fn, started_tick, failure
        return ctx, fn, started_tick, None

    def _refuse_missing_registered_function(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        fn: SyscallFn | None,
        started_tick: int,
    ) -> SyscallResult | None:
        """Fail closed if registry resolution breaks its preparation invariant."""
        if fn is not None:
            return None
        failure = self._failure_from_error(
            ctx,
            SyscallValidationError(
                "registered syscall resolution failed",
                code=ErrorCode.UNKNOWN_SYSCALL,
                origin=ErrorOrigin(
                    component="SyscallHandler",
                    subsystem="kernel.syscall",
                    syscall=syscall.name,
                ),
                details={
                    "syscall": syscall.name,
                    "reason_code": "registered_syscall_resolution_failed",
                },
            ),
        )
        self._safe_journal(ctx, syscall, failure, started_tick)
        return failure

    def _authorize_registered_call(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        descriptor: Any,
        started_tick: int,
    ) -> tuple[str | None, SyscallResult | None]:
        if descriptor is None or descriptor.access is None:
            return None, None
        try:
            access_ctx = descriptor.access(syscall.args, self.services)
            verdict = self.authorization_service.decide(access_ctx)
        except Exception as exc:
            failure = self._failure_from_error(
                ctx,
                ArvisSecurityError(
                    "authorization machinery failure; the syscall is refused "
                    "(fail-closed)",
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
            self._safe_journal(ctx, syscall, failure, started_tick)
            return None, failure
        if verdict.allowed:
            return verdict.reason_code, None

        failure = self._failure_from_error(
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
                    "reason_code": verdict.reason_code or ACCESS_DENIED_REASON_CODE,
                },
            ),
        )
        self._safe_journal(ctx, syscall, failure, started_tick)
        return verdict.reason_code, failure

    def _validate_effect_identity(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        started_tick: int,
        *,
        is_effect: bool,
        tool_authorization: ToolAuthorizationOutcome | None,
    ) -> SyscallResult | None:
        if not is_effect or not self.services.require_authenticated_principal:
            return None
        principal = principal_from_context(ctx)
        authenticated = authenticated_principal_from_context(ctx)
        turn_user_id = getattr(ctx, "user_id", None)
        identity_valid = principal is KERNEL_PRINCIPAL or (
            authenticated is not None
            and isinstance(turn_user_id, str)
            and authenticated.user_id == turn_user_id
        )
        if identity_valid:
            return None

        self._abort_tool_authorization(tool_authorization)
        failure = self._failure_from_error(
            ctx,
            ArvisSecurityError(
                "effect refused: production requires a host-authenticated principal",
                origin=ErrorOrigin(
                    component="SyscallHandler",
                    subsystem="kernel.syscall",
                    syscall=syscall.name,
                ),
                details={
                    "syscall": syscall.name,
                    "reason_code": "authenticated_principal_required",
                },
            ),
        )
        self._safe_journal(ctx, syscall, failure, started_tick)
        return failure

    def _validate_tool_effect_context(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        started_tick: int,
        outcome: ToolAuthorizationOutcome | None,
    ) -> SyscallResult | None:
        """Refuse a capability presented outside its sealed identity context."""
        if outcome is None or outcome.authorized is None:
            return None

        sealed = outcome.authorized.invocation.effect_context
        current = build_authorized_effect_context(
            ctx,
            process_id=resolve_process_id(ctx),
            run_id=resolve_run_id(ctx),
        )
        compared_fields = (
            "principal",
            "tenant",
            "authentication_source",
            "authentication_strength",
            "service_id",
            "session_id_hash",
            "process_id",
            "run_id",
            "host_binding_commitment",
        )
        mismatches = {
            field_name
            for field_name in compared_fields
            if getattr(current, field_name) != getattr(sealed, field_name)
        }

        # ``begin_run`` is kernel-owned envelope state. Whenever authorization
        # sealed a run, it must equal the handler's run.
        #
        # A sealed context carrying NO run is tolerated outside production:
        # a direct local composition may legitimately omit the binding. Under
        # production posture it is refused, because the effect would otherwise
        # execute under a run its own sealed context does not name, leaving
        # the intent's run and the effect's run with nothing tying them
        # together in the audit trail.
        if self._current_run_id is not None and sealed.run_id != self._current_run_id:
            if (
                sealed.run_id is not None
                or self.services.require_authenticated_principal
            ):
                mismatches.add("run_id")

        # The reserved kernel identity may own internal syscalls only. It is
        # never a valid identity for a user-facing tool effect.
        if sealed.principal == KERNEL_OWNER_ID or current.principal == KERNEL_OWNER_ID:
            mismatches.add("kernel_principal")

        if not mismatches:
            return None

        self._abort_tool_authorization(outcome)
        failure = self._failure_from_error(
            ctx,
            ArvisSecurityError(
                "tool effect refused: current identity does not match the "
                "authorized effect context",
                origin=ErrorOrigin(
                    component="SyscallHandler",
                    subsystem="kernel.syscall",
                    syscall=syscall.name,
                ),
                details={
                    "syscall": syscall.name,
                    "reason_code": "effect_context_mismatch",
                    # Field names support diagnosis without leaking identity
                    # values, tenant names or session commitments.
                    "mismatch_fields": ",".join(sorted(mismatches)),
                },
            ),
        )
        self._safe_journal(ctx, syscall, failure, started_tick)
        return failure

    def _abort_presented_tool_authorization(self, syscall: Syscall) -> None:
        """Revoke an owned capability even when access admission fails first."""
        if syscall.name != "tool.execute":
            return
        candidate = syscall.args.get("authorization")
        effect_boundary = self._tool_effect_boundary
        if (
            type(candidate) is ToolAuthorizationOutcome
            and candidate.authorized is not None
            and effect_boundary is not None
            and effect_boundary.owns_outcome(candidate)
        ):
            effect_boundary.abort_authorized(candidate.authorized)

    def _open_effect_transaction(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        causal_id: str,
        started_tick: int,
        *,
        authorization_reason_code: str | None,
        tool_authorization: ToolAuthorizationOutcome | None,
    ) -> SyscallResult | None:
        recorded, refusal = self._record_intent(
            ctx,
            syscall,
            causal_id,
            started_tick,
            authorization_reason_code=authorization_reason_code,
            tool_authorization=tool_authorization,
        )
        if refusal is not None:
            self._abort_tool_authorization(tool_authorization)
            self._safe_journal(ctx, syscall, refusal, started_tick)
            return refusal

        activation_refusal = self._activate_tool_authorization(
            ctx,
            syscall,
            tool_authorization,
            recorded,
        )
        if activation_refusal is not None:
            self._journal_effect_result(
                ctx,
                syscall,
                activation_refusal,
                started_tick,
            )
        return activation_refusal

    def _invoke_and_journal(
        self,
        *,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        fn: SyscallFn,
        causal_id: str,
        started_tick: int,
        is_effect: bool,
        tool_authorization: ToolAuthorizationOutcome | None,
    ) -> SyscallResult:
        try:
            call_args = {**syscall.args, "causal_id": causal_id}
            if tool_authorization is not None:
                call_args["authorization"] = tool_authorization
            result = fn(self, **call_args)
        except Exception as exc:
            self._abort_tool_authorization(tool_authorization)
            failure = self._failure_from_exception(
                ctx,
                exc,
                syscall_name=syscall.name,
            )
            if is_effect:
                self._journal_effect_result(ctx, syscall, failure, started_tick)
            else:
                self._safe_journal(ctx, syscall, failure, started_tick)
            return failure

        if not isinstance(result, SyscallResult):
            self._abort_tool_authorization(tool_authorization)
            result = self._failure_from_error(
                ctx,
                SyscallValidationError(
                    f"Invalid syscall return type: {type(result).__name__}",
                    code=ErrorCode.INVALID_SYSCALL_RETURN_TYPE,
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "return_type": type(result).__name__,
                    },
                ),
            )
        if is_effect:
            self._journal_effect_result(ctx, syscall, result, started_tick)
        else:
            self._safe_journal(ctx, syscall, result, started_tick)
        return result

    def _validate_tool_authorization_outcome(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
    ) -> tuple[ToolAuthorizationOutcome | None, SyscallResult | None]:
        """Copy one trusted authorization outcome into the kernel boundary.

        The caller-owned object is never reused after validation. This closes a
        TOCTOU window where a callback retaining the original outcome could swap
        its capability after the intent digest but before the syscall body.
        """
        candidate = syscall.args.get("authorization")
        if type(candidate) is not ToolAuthorizationOutcome:
            return None, self._failure_from_error(
                ctx,
                SyscallValidationError(
                    "tool.execute requires an exact authorization outcome",
                    code=ErrorCode.INVALID_SYSCALL_ARGS,
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "invalid_tool_authorization_outcome",
                        "authorization_type": type(candidate).__name__,
                    },
                ),
            )

        try:
            if candidate.authorized is not None:
                trusted = ToolAuthorizationOutcome(
                    authorized=candidate.authorized,
                )
            else:
                trusted = ToolAuthorizationOutcome(
                    refusal=candidate.refusal,
                    refusal_snapshot=candidate.refusal_snapshot,
                )
        except (TypeError, ValueError) as exc:
            return None, self._failure_from_error(
                ctx,
                SyscallValidationError(
                    "tool authorization outcome violates its invariant",
                    code=ErrorCode.INVALID_SYSCALL_ARGS,
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "invalid_tool_authorization_outcome",
                        "exception_type": type(exc).__name__,
                    },
                ),
            )

        effect_boundary = self._tool_effect_boundary
        if effect_boundary is None or not effect_boundary.owns_outcome(trusted):
            return None, self._failure_from_error(
                ctx,
                ArvisSecurityError(
                    "tool authorization outcome is not owned by the configured manager",
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "untrusted_tool_authorization_outcome",
                    },
                ),
            )

        return trusted, None

    def _abort_tool_authorization(
        self,
        outcome: ToolAuthorizationOutcome | None,
    ) -> None:
        """Best-effort abort of a manager-owned pre-effect capability."""
        if outcome is None or outcome.authorized is None:
            return
        effect_boundary = self._tool_effect_boundary
        if effect_boundary is not None:
            effect_boundary.abort_authorized(outcome.authorized)

    def _execute_tool_authorized(
        self,
        authorized: Any,
        result: Any,
        ctx: Any,
    ) -> Any:
        """Execute through the private boundary permit claimed at composition."""
        effect_boundary = self._tool_effect_boundary
        if effect_boundary is None:
            raise UnauthorizedExecutionError("tool manager not configured")
        return effect_boundary.execute_authorized(authorized, result, ctx)

    def _activate_tool_authorization(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        outcome: ToolAuthorizationOutcome | None,
        recorded: RecordedIntent | None,
    ) -> SyscallResult | None:
        """Activate the exact capability only after intent acceptance."""
        if outcome is None or outcome.authorized is None:
            return None
        if recorded is None:
            self._abort_tool_authorization(outcome)
            return self._failure_from_error(
                ctx,
                ArvisSecurityError(
                    "tool capability activation requires an accepted intent",
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "capability_activation_failed",
                    },
                ),
            )

        effect_boundary = self._tool_effect_boundary
        if effect_boundary is None:
            self._abort_tool_authorization(outcome)
            return self._failure_from_error(
                ctx,
                ArvisSecurityError(
                    "configured tool manager cannot activate capabilities",
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "capability_activation_failed",
                    },
                ),
            )

        try:
            activated = bool(
                effect_boundary.activate_authorized(
                    outcome.authorized,
                    receipt=recorded.receipt,
                    intent_sha256=recorded.intent_sha256,
                    run_id=recorded.run_id,
                    causal_id=recorded.causal_id,
                )
            )
        except Exception as exc:
            self._abort_tool_authorization(outcome)
            return self._failure_from_error(
                ctx,
                ArvisSecurityError(
                    "tool capability activation failed before the effect",
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "capability_activation_failed",
                        "exception_type": type(exc).__name__,
                    },
                ),
            )
        if activated:
            return None

        self._abort_tool_authorization(outcome)
        return self._failure_from_error(
            ctx,
            ArvisSecurityError(
                "tool capability was not activated by the accepted intent",
                origin=ErrorOrigin(
                    component="SyscallHandler",
                    subsystem="kernel.syscall",
                    syscall=syscall.name,
                ),
                details={
                    "syscall": syscall.name,
                    "reason_code": "capability_activation_failed",
                },
            ),
        )

    def _record_intent(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        causal_id: str,
        started_tick: int,
        *,
        authorization_reason_code: str | None = None,
        tool_authorization: ToolAuthorizationOutcome | None = None,
    ) -> tuple[RecordedIntent | None, SyscallResult | None]:
        """Delegate exact intent persistence to the typed outbox service."""
        try:
            recorded = self._intent_outbox.record(
                ctx=ctx,
                syscall=syscall,
                causal_id=causal_id,
                started_tick=started_tick,
                current_run_id=self._current_run_id,
                authorization_reason_code=authorization_reason_code,
                tool_authorization=tool_authorization,
                engagement_digest_fn=effect_engagement_digest,
            )
            return recorded, None
        except IntentOutboxRefusal as exc:
            details = {"syscall": syscall.name, **exc.details}
            details["reason_code"] = exc.reason_code
            return None, self._failure_from_error(
                ctx,
                ArvisSecurityError(
                    exc.message,
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details=details,
                ),
            )
        except Exception as exc:
            return None, self._failure_from_error(
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

    def _journal_effect_result(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        result: SyscallResult,
        started_tick: int,
    ) -> None:
        """Mandatory result journal after an effect (P0-1-a6).

        The effect has happened; a journaling failure cannot refuse it
        retroactively. It marks the run AUDIT_INCOMPLETE instead: the
        intent/result bijection check refuses the commitment
        downstream, REQUIRED refuses the public result, and the
        incompleteness is never silent.
        """
        try:
            self._journal(ctx, syscall, result, started_tick)
        except Exception as exc:  # arvis-broad: marks audit incompleteness
            self._mark_audit_incomplete(ctx, syscall, exc)

    def _mark_audit_incomplete(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        exc: Exception,
    ) -> None:
        if ctx is None:
            return
        try:
            ctx.extra["audit_incomplete"] = True
            entries = ctx.extra.setdefault("audit_incomplete_syscalls", [])
            if isinstance(entries, list):
                entries.append(
                    {
                        "syscall": syscall.name,
                        "exception_type": type(exc).__name__,
                    }
                )
            execution_state = _execution_state_from_ctx(ctx)
            if execution_state is not None:
                execution_state.metadata["audit_incomplete"] = True
            ErrorManager.attach(
                ctx,
                SyscallExecutionError(
                    "Effect result journaling failure: audit incomplete",
                    origin=ErrorOrigin(
                        component="SyscallHandler",
                        subsystem="kernel.syscall",
                        syscall=syscall.name,
                    ),
                    details={
                        "syscall": syscall.name,
                        "reason_code": "audit_incomplete",
                        "exception_type": type(exc).__name__,
                    },
                    cause=normalize_error(exc).cause,
                ),
            )
        except Exception:  # arvis-broad: last resort, context unwritable
            # The orphan-intent bijection check still catches the
            # missing pair downstream, so the incompleteness stays
            # detectable.
            pass

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

        # Campaign 6 (Lot 5): the run identity is journaled on every
        # result, mirroring the intent side.
        if self._current_run_id is not None:
            entry["run_id"] = self._current_run_id

        # Campaign 6 (Lot 2, closes a8 section 9): an effect result
        # carries the EXACT engagement digest of its intent, popped
        # single-use by causal id. The bijection verifies the equality;
        # the journal digest binds the pair; a permuted result can no
        # longer close a different intent.
        intent_commitment = self._pending_intent_commitments.pop(syscall_id, None)
        if intent_commitment is not None:
            entry["intent_commitment_sha256"] = intent_commitment

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
        """Causal id of a syscall, globally unique across runs.

        Campaign 7 (Lot 7) binds the complete run identity. The previous
        twelve-hex-character prefix exposed only 48 bits and let two distinct
        runs sharing that prefix produce the same local causal ids. Outside a
        runtime-entered run the legacy shape is kept for direct compositions.
        """
        process_id = syscall.args.get("process_id", "none")
        if self._current_run_id is not None:
            return (
                f"syscall:{self._current_run_id}:"
                f"{syscall.name}:{process_id}:{tick}:{seq}"
            )
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
