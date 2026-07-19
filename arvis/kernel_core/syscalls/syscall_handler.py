# arvis/kernel_core/syscalls/syscall_handler.py

from __future__ import annotations

import inspect
import threading
from dataclasses import dataclass
from typing import Any, Protocol

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
from arvis.kernel_core.access.models import KERNEL_PRINCIPAL
from arvis.kernel_core.access.policy import (
    ACCESS_DENIED_REASON_CODE,
    AuthorizationPolicy,
    OwnerScopedAuthorization,
)
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.audit_sink import (
    AuditReceipt,
    AuditSinkManifest,
    InMemoryAuditSink,
    production_sink_manifest,
    validate_receipt,
)
from arvis.kernel_core.syscalls.engagement import (
    effect_engagement_digest,
    effect_parameters_from_result,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    SyscallFn,
    get_descriptor,
    get_syscall,
)
from arvis.tools.manager import ToolAuthorizationOutcome


class RuntimeStateLike(Protocol):
    scheduler_state: Any

    def append_event(self, name: str, payload: dict[str, Any]) -> None: ...


class PipelineContextLike(Protocol):
    extra: dict[str, Any]


@dataclass(frozen=True, slots=True)
class _RecordedIntent:
    """Exact outbox acceptance used to activate a tool capability."""

    receipt: AuditReceipt
    intent_sha256: str
    run_id: str | None
    causal_id: str


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
        # Campaign 7 (Lot 4): even development/test compositions with no
        # host sink use a concrete volatile outbox. This preserves the
        # universal MINTED -> receipt-bound ACTIVATED transition; Lot 6
        # separately qualifies which sinks count as production-durable.
        self._volatile_intent_sink = InMemoryAuditSink()
        self._accepted_durable_positions: set[tuple[str, str]] = set()
        self._durable_position_lock = threading.Lock()

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

        validated_tool_authorization: ToolAuthorizationOutcome | None = None
        if syscall.name == "tool.execute":
            (
                validated_tool_authorization,
                authorization_failure,
            ) = self._validate_tool_authorization_outcome(ctx, syscall)
            if authorization_failure is not None:
                self._safe_journal(
                    ctx,
                    syscall,
                    authorization_failure,
                    started_tick,
                )
                return authorization_failure

        is_effect = descriptor is not None and descriptor.effect is SyscallEffect.EFFECT
        if is_effect and self.services.require_authenticated_principal:
            principal = principal_from_context(ctx)
            authenticated = authenticated_principal_from_context(ctx)
            valid_kernel = principal is KERNEL_PRINCIPAL
            turn_user_id = getattr(ctx, "user_id", None)
            identity_valid = valid_kernel or (
                authenticated is not None
                and isinstance(turn_user_id, str)
                and authenticated.user_id == turn_user_id
            )
            if not identity_valid:
                self._abort_tool_authorization(validated_tool_authorization)
                refusal = self._failure_from_error(
                    ctx,
                    ArvisSecurityError(
                        "effect refused: production requires a "
                        "host-authenticated principal",
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
                self._safe_journal(ctx, syscall, refusal, started_tick)
                return refusal

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
        recorded_intent: _RecordedIntent | None = None
        if is_effect:
            recorded_intent, intent_refusal = self._record_intent(
                ctx,
                syscall,
                causal_id,
                started_tick,
                authorization_reason_code=authorization_reason_code,
                tool_authorization=validated_tool_authorization,
            )
            if intent_refusal is not None:
                self._abort_tool_authorization(validated_tool_authorization)
                self._safe_journal(ctx, syscall, intent_refusal, started_tick)
                return intent_refusal

            activation_refusal = self._activate_tool_authorization(
                ctx,
                syscall,
                validated_tool_authorization,
                recorded_intent,
            )
            if activation_refusal is not None:
                # The outbox already accepted this intent. Even though the
                # effect was refused before execution, the result must close
                # the accepted intent with its exact commitment.
                self._journal_effect_result(
                    ctx, syscall, activation_refusal, started_tick
                )
                return activation_refusal

        try:
            call_args = {
                **syscall.args,
                "causal_id": causal_id,
            }
            if validated_tool_authorization is not None:
                # Kernel-owned copy: callbacks holding the caller's original
                # outcome cannot swap the capability between intent and effect.
                call_args["authorization"] = validated_tool_authorization
            syscall_result = fn(self, **call_args)
        except Exception as exc:
            # If the tool syscall failed before its executor consumed the
            # capability, revoke it. If consumption already crossed the effect
            # boundary, abort_authorized is a no-op on the CONSUMED state.
            self._abort_tool_authorization(validated_tool_authorization)
            error_result = self._failure_from_exception(
                ctx,
                exc,
                syscall_name=syscall.name,
            )
            # P0-1-a6: past the fn call the effect may have happened;
            # the result journal is mandatory on the effect path.
            if is_effect:
                self._journal_effect_result(ctx, syscall, error_result, started_tick)
            else:
                self._safe_journal(ctx, syscall, error_result, started_tick)
            return error_result

        if not isinstance(syscall_result, SyscallResult):
            self._abort_tool_authorization(validated_tool_authorization)
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

        if is_effect:
            self._journal_effect_result(ctx, syscall, syscall_result, started_tick)
        else:
            self._safe_journal(ctx, syscall, syscall_result, started_tick)
        return syscall_result

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

        tool_manager = self.services.tool_manager
        owns_outcome = getattr(tool_manager, "owns_outcome", None)
        if not callable(owns_outcome) or not owns_outcome(trusted):
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
        manager = self.services.tool_manager
        abort = getattr(manager, "abort_authorized", None)
        if callable(abort):
            abort(outcome.authorized)

    def _activate_tool_authorization(
        self,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        outcome: ToolAuthorizationOutcome | None,
        recorded: _RecordedIntent | None,
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

        manager = self.services.tool_manager
        activate = getattr(manager, "activate_authorized", None)
        if not callable(activate):
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
                activate(
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
    ) -> tuple[_RecordedIntent | None, SyscallResult | None]:
        """Record and acknowledge an intent before an effect syscall.

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
        sink = self.services.audit_intent_sink
        sink_manifest: AuditSinkManifest | None = None
        if self.services.require_durable_intent_sink:
            manifest_reason: str | None
            if sink is None:
                manifest_reason = "durable_sink_required"
            else:
                sink_manifest, manifest_reason = production_sink_manifest(sink)
            if manifest_reason is not None or not callable(
                getattr(sink, "append", None)
            ):
                # D4-e, hardened campaign 6 (Lot 6, closes a8 section 14):
                # a profile requiring durability requires a sink that
                # PROVES it (DurableAuditSink returning receipts); a bare
                # callable only declares. The effect is refused before
                # anything runs and before anything is recorded.
                return None, self._failure_from_error(
                    ctx,
                    ArvisSecurityError(
                        "effect refused: the production profile requires a qualified "
                        "transactional append-only audit sink",
                        origin=ErrorOrigin(
                            component="SyscallHandler",
                            subsystem="kernel.syscall",
                            syscall=syscall.name,
                        ),
                        details={
                            "syscall": syscall.name,
                            "reason_code": manifest_reason or "durable_sink_required",
                        },
                    ),
                )
        else:
            candidate_manifest = getattr(sink, "manifest", None)
            if type(candidate_manifest) is AuditSinkManifest:
                sink_manifest = candidate_manifest

        intent: dict[str, Any] = {
            "kind": "syscall_intent",
            "syscall": syscall.name,
            "causal_id": causal_id,
            "tick": started_tick,
            "process_id": syscall.args.get("process_id") or "none",
        }
        # Campaign 6 (Lot 5): the run identity is journaled on the
        # intent (and on the sink copy), so a shared sink can reconcile
        # entries across runs without causal id ambiguity.
        if self._current_run_id is not None:
            intent["run_id"] = self._current_run_id
        # Campaign 5 (D-1): boundary provenance from the host context.
        # Absent when the host declares none, so the journaled entry
        # stays byte-identical. The label never enters the engagement
        # digest (which binds effect parameters, not boundary identity)
        # nor the timeline commitment; it lives only on the journaled
        # intent and the sink copy.
        if self.services.instance_label is not None:
            intent["instance_label"] = self.services.instance_label
        try:
            # P0-3-a6: engage the exact parameters of the effect BEFORE
            # it runs. The digest binds the materialized redacted
            # arguments, the principal, the tenant, the turn owner and
            # the authorization outcome; only the hash enters the
            # journal, never the parameters themselves (ZKCS).
            args_ctx = syscall.args.get("ctx")
            principal = principal_from_context(args_ctx)
            authenticated = authenticated_principal_from_context(args_ctx)
            # Campaign 6 (Lot 1, closes a8 P0 section 8): the intent
            # binds the authorization verdict from the SEALED outcome
            # computed before this syscall was issued: the snapshot on
            # the minted capability for an allowed invocation, the
            # denial material for a refusal. The mutable ctx.extra
            # channel is gone; a stale decision from an earlier call is
            # not reachable by construction.
            authorization_snapshot: dict[str, Any] | None = None
            effect_invocation = None
            if syscall.name == "tool.execute":
                # The strict, manager-owned, kernel-copied outcome was resolved
                # before the intent phase. Never re-read the caller-owned object.
                assert tool_authorization is not None
                if tool_authorization.authorized is not None:
                    effect_invocation = tool_authorization.authorized.invocation
                    authorization_snapshot = dict(
                        tool_authorization.authorized.authorization_snapshot
                    )
                else:
                    assert tool_authorization.refusal_snapshot is not None
                    authorization_snapshot = (
                        tool_authorization.refusal_snapshot.to_material()
                    )
            # Campaign 6 (Lot 0/1): runtime objects (pipeline result,
            # authorization outcome) are runtime bindings with no
            # injective encoding; the digest binds the extracted effect
            # parameters instead, from the sealed invocation when one
            # exists, from the decided action otherwise, never a
            # partial view of runtime state.
            digest_args = dict(syscall.args)
            digest_args.pop("authorization", None)
            if effect_invocation is not None:
                # Campaign 7 (Lot 1): the intent binds the canonical hash
                # captured by the frozen invocation. It never rematerializes or
                # rereads the caller-owned payload, so authorization, outbox and
                # execution all refer to one immutable effect object.
                digest_args["result"] = {
                    "tool": effect_invocation.tool_name,
                    "tool_payload_sha256": effect_invocation.payload_sha256,
                    # Campaign 7 (Lot 7): the externally reusable operation
                    # identity is part of WHAT was durably accepted. The key
                    # is deterministic for one logical action and therefore
                    # remains stable across retries and crash recovery.
                    "idempotency_key": effect_invocation.idempotency_key,
                }
                if effect_invocation.idempotency_key is not None:
                    intent["idempotency_key"] = effect_invocation.idempotency_key
            elif "result" in digest_args:
                digest_args["result"] = effect_parameters_from_result(
                    digest_args["result"]
                )
            intent["commitment_sha256"] = effect_engagement_digest(
                syscall_name=syscall.name,
                args=digest_args,
                principal_user_id=(
                    principal.user_id if principal is not None else None
                ),
                principal_organization_id=(
                    principal.organization_id if principal is not None else None
                ),
                turn_user_id=getattr(args_ctx, "user_id", None),
                authorization_reason_code=authorization_reason_code,
                authorization_snapshot=authorization_snapshot,
                principal_authentication_source=(
                    authenticated.authentication_source
                    if authenticated is not None
                    else None
                ),
                principal_authentication_strength=(
                    authenticated.authentication_strength
                    if authenticated is not None
                    else None
                ),
                principal_service_id=(
                    authenticated.service_id if authenticated is not None else None
                ),
                principal_session_id_hash=(
                    authenticated.session_id_hash if authenticated is not None else None
                ),
            )
            # The host outbox accepts the complete engagement first. Local
            # journals and the pending result binding are published only after
            # a valid receipt exists, so an outbox rejection leaves no phantom
            # accepted intent or leaked pending commitment.
            receipt: Any
            if sink is None:
                receipt = self._volatile_intent_sink.append(dict(intent))
            else:
                append = getattr(sink, "append", None)
                if callable(append):
                    # The configured sink answers with the exact acceptance
                    # that will activate the capability. Any malformed or
                    # mismatched receipt aborts the transaction.
                    receipt = append(dict(intent))
                else:
                    # Legacy callable sink: preserve its notification outside
                    # durability-required profiles, then obtain a concrete
                    # volatile receipt for the capability transaction.
                    sink(dict(intent))
                    receipt = self._volatile_intent_sink.append(dict(intent))

            invalid_reason = validate_receipt(
                receipt,
                intent,
                manifest=sink_manifest,
            )
            if invalid_reason is not None:
                return None, self._failure_from_error(
                    ctx,
                    ArvisSecurityError(
                        "effect refused: the intent sink did not return a "
                        "valid receipt for this intent (fail-closed)",
                        origin=ErrorOrigin(
                            component="SyscallHandler",
                            subsystem="kernel.syscall",
                            syscall=syscall.name,
                        ),
                        details={
                            "syscall": syscall.name,
                            "reason_code": "invalid_audit_receipt",
                            "receipt_reason": invalid_reason,
                        },
                    ),
                )
            durable_position = (receipt.store_fingerprint, receipt.durable_position)
            with self._durable_position_lock:
                if durable_position in self._accepted_durable_positions:
                    return None, self._failure_from_error(
                        ctx,
                        ArvisSecurityError(
                            "effect refused: durable position was already acknowledged",
                            origin=ErrorOrigin(
                                component="SyscallHandler",
                                subsystem="kernel.syscall",
                                syscall=syscall.name,
                            ),
                            details={
                                "syscall": syscall.name,
                                "reason_code": "audit_receipt_position_reused",
                            },
                        ),
                    )
                self._accepted_durable_positions.add(durable_position)
            assert type(receipt) is AuditReceipt
            # Envelope material: commitment binds WHAT was accepted; receipt
            # binds WHERE and under which run the acceptance lives.
            intent["audit_receipt"] = receipt.to_material()
            # Campaign 6 (Lot 2): remember this accepted intent's exact digest
            # so the paired result journals it (cryptographic binding).
            self._pending_intent_commitments[causal_id] = intent["commitment_sha256"]
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
            return (
                _RecordedIntent(
                    receipt=receipt,
                    intent_sha256=intent["commitment_sha256"],
                    run_id=intent.get("run_id"),
                    causal_id=causal_id,
                ),
                None,
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
