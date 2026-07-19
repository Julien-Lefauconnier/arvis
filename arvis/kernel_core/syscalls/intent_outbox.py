"""Transactional pre-effect intent outbox service.

The service owns intent construction, engagement, sink qualification, receipt
validation, durable-position replay protection and publication to local runtime
journals. ``SyscallHandler`` remains the transaction coordinator.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from arvis.kernel_core.access.identity import (
    authenticated_principal_from_context,
    principal_from_context,
)
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
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.tools.manager import ToolAuthorizationOutcome


class RuntimeStateLike(Protocol):
    """Minimal runtime event surface required by the outbox."""

    def append_event(self, name: str, payload: dict[str, Any]) -> None: ...


class PipelineContextLike(Protocol):
    """Minimal journal surface required by the outbox."""

    extra: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RecordedIntent:
    """Exact outbox acceptance used to activate a tool capability."""

    receipt: AuditReceipt
    intent_sha256: str
    run_id: str | None
    causal_id: str


class IntentOutboxRefusal(RuntimeError):
    """Expected fail-closed refusal with stable public reason material."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.reason_code = reason_code
        self.details = dict(details or {})


def _execution_state_from_ctx(ctx: Any) -> Any | None:
    execution = getattr(ctx, "execution", None)
    runtime = getattr(execution, "execution_state", None)
    if runtime is not None:
        return runtime
    return getattr(ctx, "execution_state", None)


class IntentOutboxService:
    """Persist and publish one exact pre-effect intent."""

    def __init__(
        self,
        *,
        services: KernelServiceRegistry,
        runtime_state: RuntimeStateLike | None,
        pending_intent_commitments: dict[str, str],
    ) -> None:
        self._services = services
        self._runtime_state = runtime_state
        self._pending_intent_commitments = pending_intent_commitments
        self._volatile_sink = InMemoryAuditSink()
        self._accepted_positions: set[tuple[str, str]] = set()
        self._position_lock = threading.Lock()

    def record(
        self,
        *,
        ctx: PipelineContextLike | None,
        syscall: Syscall,
        causal_id: str,
        started_tick: int,
        current_run_id: str | None,
        authorization_reason_code: str | None,
        tool_authorization: ToolAuthorizationOutcome | None,
        engagement_digest_fn: Callable[..., str] = effect_engagement_digest,
    ) -> RecordedIntent:
        """Record, acknowledge and publish one intent before its effect."""
        sink = self._services.audit_intent_sink
        manifest = self._qualify_sink(sink, syscall)
        intent = self._build_intent(
            syscall=syscall,
            causal_id=causal_id,
            started_tick=started_tick,
            current_run_id=current_run_id,
        )
        self._engage(
            intent=intent,
            syscall=syscall,
            authorization_reason_code=authorization_reason_code,
            tool_authorization=tool_authorization,
            engagement_digest_fn=engagement_digest_fn,
        )
        receipt = self._append_and_validate(
            sink=sink,
            manifest=manifest,
            intent=intent,
            syscall=syscall,
        )
        self._claim_durable_position(receipt, syscall)
        intent["audit_receipt"] = receipt.to_material()
        self._publish(
            ctx=ctx,
            intent=intent,
            receipt=receipt,
            syscall=syscall,
            causal_id=causal_id,
            started_tick=started_tick,
        )
        return RecordedIntent(
            receipt=receipt,
            intent_sha256=intent["commitment_sha256"],
            run_id=intent.get("run_id"),
            causal_id=causal_id,
        )

    def _qualify_sink(
        self,
        sink: Any,
        syscall: Syscall,
    ) -> AuditSinkManifest | None:
        if self._services.require_durable_intent_sink:
            manifest: AuditSinkManifest | None = None
            reason: str | None
            if sink is None:
                reason = "durable_sink_required"
            else:
                manifest, reason = production_sink_manifest(sink)
            if reason is not None or not callable(getattr(sink, "append", None)):
                raise IntentOutboxRefusal(
                    "effect refused: the production profile requires a qualified "
                    "transactional append-only audit sink",
                    reason_code=reason or "durable_sink_required",
                    details={"syscall": syscall.name},
                )
            return manifest

        candidate = getattr(sink, "manifest", None)
        return candidate if type(candidate) is AuditSinkManifest else None

    def _build_intent(
        self,
        *,
        syscall: Syscall,
        causal_id: str,
        started_tick: int,
        current_run_id: str | None,
    ) -> dict[str, Any]:
        intent: dict[str, Any] = {
            "kind": "syscall_intent",
            "syscall": syscall.name,
            "causal_id": causal_id,
            "tick": started_tick,
            "process_id": syscall.args.get("process_id") or "none",
        }
        if current_run_id is not None:
            intent["run_id"] = current_run_id
        if self._services.instance_label is not None:
            intent["instance_label"] = self._services.instance_label
        return intent

    @staticmethod
    def _engage(
        *,
        intent: dict[str, Any],
        syscall: Syscall,
        authorization_reason_code: str | None,
        tool_authorization: ToolAuthorizationOutcome | None,
        engagement_digest_fn: Callable[..., str],
    ) -> None:
        args_ctx = syscall.args.get("ctx")
        principal = principal_from_context(args_ctx)
        authenticated = authenticated_principal_from_context(args_ctx)
        authorization_snapshot: dict[str, Any] | None = None
        authorized_effect_context: dict[str, Any] | None = None
        effect_invocation = None

        if syscall.name == "tool.execute":
            if tool_authorization is None:
                raise ValueError("tool effect requires a validated authorization")
            if tool_authorization.authorized is not None:
                effect_invocation = tool_authorization.authorized.invocation
                authorization_snapshot = dict(
                    tool_authorization.authorized.authorization_snapshot
                )
                authorized_effect_context = (
                    effect_invocation.effect_context.to_material()
                )
                intent["effect_context"] = dict(authorized_effect_context)
                intent["effect_context_commitment"] = (
                    effect_invocation.effect_context.commitment_sha256
                )
            else:
                if tool_authorization.refusal_snapshot is None:
                    raise ValueError("tool refusal requires an authorization snapshot")
                authorization_snapshot = (
                    tool_authorization.refusal_snapshot.to_material()
                )

        digest_args = dict(syscall.args)
        digest_args.pop("authorization", None)
        if effect_invocation is not None:
            digest_args["result"] = {
                "tool": effect_invocation.tool_name,
                "tool_payload_sha256": effect_invocation.payload_sha256,
                "idempotency_key": effect_invocation.idempotency_key,
            }
            if effect_invocation.idempotency_key is not None:
                intent["idempotency_key"] = effect_invocation.idempotency_key
        elif "result" in digest_args:
            digest_args["result"] = effect_parameters_from_result(digest_args["result"])

        intent["commitment_sha256"] = engagement_digest_fn(
            syscall_name=syscall.name,
            args=digest_args,
            principal_user_id=principal.user_id if principal is not None else None,
            principal_organization_id=(
                principal.organization_id if principal is not None else None
            ),
            turn_user_id=getattr(args_ctx, "user_id", None),
            authorization_reason_code=authorization_reason_code,
            authorization_snapshot=authorization_snapshot,
            authorized_effect_context=authorized_effect_context,
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

    def _append_and_validate(
        self,
        *,
        sink: Any,
        manifest: AuditSinkManifest | None,
        intent: dict[str, Any],
        syscall: Syscall,
    ) -> AuditReceipt:
        if sink is None:
            receipt: Any = self._volatile_sink.append(dict(intent))
        else:
            append = getattr(sink, "append", None)
            if callable(append):
                receipt = append(dict(intent))
            else:
                sink(dict(intent))
                receipt = self._volatile_sink.append(dict(intent))

        invalid_reason = validate_receipt(receipt, intent, manifest=manifest)
        if invalid_reason is not None:
            raise IntentOutboxRefusal(
                "effect refused: the intent sink did not return a valid receipt "
                "for this intent (fail-closed)",
                reason_code="invalid_audit_receipt",
                details={
                    "syscall": syscall.name,
                    "receipt_reason": invalid_reason,
                },
            )
        if type(receipt) is not AuditReceipt:
            raise TypeError("validated audit receipt has an invalid type")
        return receipt

    def _claim_durable_position(
        self,
        receipt: AuditReceipt,
        syscall: Syscall,
    ) -> None:
        position = (receipt.store_fingerprint, receipt.durable_position)
        with self._position_lock:
            if position in self._accepted_positions:
                raise IntentOutboxRefusal(
                    "effect refused: durable position was already acknowledged",
                    reason_code="audit_receipt_position_reused",
                    details={"syscall": syscall.name},
                )
            self._accepted_positions.add(position)

    def _publish(
        self,
        *,
        ctx: PipelineContextLike | None,
        intent: dict[str, Any],
        receipt: AuditReceipt,
        syscall: Syscall,
        causal_id: str,
        started_tick: int,
    ) -> None:
        del receipt
        self._pending_intent_commitments[causal_id] = intent["commitment_sha256"]
        if ctx is not None:
            intents = ctx.extra.setdefault("syscall_intents", [])
            if isinstance(intents, list):
                intents.append(intent)
            execution_state = _execution_state_from_ctx(ctx)
            state_intents = getattr(execution_state, "syscall_intents", None)
            if isinstance(state_intents, list):
                state_intents.append(intent)
        if self._runtime_state is not None:
            self._runtime_state.append_event(
                "syscall_intent",
                {
                    "process_id": intent["process_id"],
                    "syscall_id": causal_id,
                    "syscall_name": syscall.name,
                    "tick": started_tick,
                    "causal_id": causal_id,
                },
            )


__all__ = [
    "IntentOutboxRefusal",
    "IntentOutboxService",
    "PipelineContextLike",
    "RecordedIntent",
    "RuntimeStateLike",
]
