# arvis/tools/manager.py
"""Tool lifecycle: authorization BEFORE the syscall intent (campaign 6).

The a8 audit (P0, section 8) proved the pre-effect intent was recorded
before the business authorization existed: the syscall handler built
and journaled the intent, THEN the tool body ran the manager, which
reserved the confirmation, evaluated ToolPolicy and only then attached
the authorization snapshot to a mutable ``ctx.extra`` channel. The
intent of call N bound the snapshot of call N-1, or none.

Campaign 6 reorders the chain. :meth:`ToolManager.authorize` runs the
FULL pre-effect authorization before any syscall is issued:

    extraction -> tool lookup -> input schema -> principal/tenant
    -> confirmation reservation -> ToolPolicy
    -> immutable ToolAuthorizationSnapshot
    -> sealed AuthorizedInvocation carrying the snapshot

and returns a frozen :class:`ToolAuthorizationOutcome` (a sealed
capability, or a pre-effect refusal with its own denial snapshot). The
runtime threads the outcome into the ``tool.execute`` syscall args; the
handler binds the intent from the sealed capability, never from a
mutable channel; the syscall body then calls
:meth:`execute_authorized`, which runs the executor and finalizes the
confirmation on the effect boundary: committed only if the boundary was
crossed, released on any pre-effect refusal (closes constat 11).
"""

from dataclasses import dataclass
from typing import Any

from arvis.adapters.tools.authorization import ToolAuthorizationDecision
from arvis.adapters.tools.authorization_snapshot import ToolAuthorizationSnapshot
from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.adapters.tools.invocation import (
    FrozenEffectPayload,
    FrozenEffectPayloadError,
    ToolInvocation,
)
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.errors.tool_runtime import (
    ToolAuthorizationError,
    ToolInputValidationError,
    UnknownToolError,
)
from arvis.kernel_core.access.identity import (
    authenticated_principal_from_context,
    principal_from_context,
)
from arvis.kernel_core.syscalls.audit_sink import (
    AuditReceipt,
    InMemoryAuditSink,
    validate_receipt,
)
from arvis.kernel_core.syscalls.engagement import stable_hash
from arvis.tools.authorized_invocation import (
    AuthorizedInvocation,
    CapabilityActivationBinding,
    CapabilityState,
    UnauthorizedExecutionError,
)
from arvis.tools.confirmation import (
    ConfirmationRegistry,
    ConfirmationReservation,
    payload_commitment,
)
from arvis.tools.executor import ToolExecutor, _schema_violation
from arvis.tools.registry import ToolRegistry
from arvis.tools.runtime.runtime_bindings import resolve_process_id
from arvis.tools.tool_result import (
    EFFECT_NOT_STARTED,
    PRE_EFFECT_REFUSAL,
    ToolEffectState,
    ToolResult,
)


def _resolve_turn_risk(ctx: Any) -> float:
    """Real risk of the current turn, for the invocation (F-006-a5).

    Hardening composition of the available signals: the declared input
    risk (untrusted, may only make policy stricter) and the assessed
    collapse risk. Returns 0.0 only when no signal is available, which
    keeps the max_risk policy conservative rather than silent.
    """
    candidates: list[float] = []
    extra = getattr(ctx, "extra", None)
    if isinstance(extra, dict):
        declared = extra.get("input_risk")
        if isinstance(declared, (int, float)) and not isinstance(declared, bool):
            candidates.append(float(declared))
    assessed = getattr(ctx, "collapse_risk", None)
    if assessed is not None:
        try:
            candidates.append(float(assessed))
        except (TypeError, ValueError):
            pass
    if not candidates:
        return 0.0
    return max(0.0, min(1.0, max(candidates)))


@dataclass(frozen=True, slots=True)
class ToolAuthorizationOutcome:
    """Strict result of the pre-syscall authorization phase.

    Exactly one path exists:

    - an exact :class:`AuthorizedInvocation`, whose own immutable snapshot
      is the sole source of allowed authorization material; or
    - a pre-effect :class:`ToolResult` refusal paired with the immutable
      denial snapshot that produced it.

    The invariant is enforced at construction. Generic wrappers and
    partially populated outcomes are not valid transport objects.
    """

    authorized: AuthorizedInvocation | None = None
    refusal: ToolResult | None = None
    refusal_snapshot: ToolAuthorizationSnapshot | None = None

    def __post_init__(self) -> None:
        has_authorized = self.authorized is not None
        has_refusal = self.refusal is not None

        if has_authorized == has_refusal:
            raise ValueError(
                "a tool authorization outcome must contain exactly one of "
                "authorized or refusal"
            )

        if has_authorized:
            if type(self.authorized) is not AuthorizedInvocation:
                raise TypeError("authorized must be an exact AuthorizedInvocation")
            if self.refusal_snapshot is not None:
                raise ValueError(
                    "an authorized outcome cannot carry a separate refusal snapshot"
                )
            return

        if type(self.refusal) is not ToolResult:
            raise TypeError("refusal must be an exact ToolResult")
        if type(self.refusal_snapshot) is not ToolAuthorizationSnapshot:
            raise TypeError(
                "a refusal outcome requires an exact ToolAuthorizationSnapshot"
            )
        if self.refusal_snapshot.allowed:
            raise ValueError("a refusal snapshot cannot be allowed")
        if self.refusal_snapshot.tool_name != self.refusal.tool_name:
            raise ValueError(
                "the refusal result and refusal snapshot must name the same tool"
            )

    @property
    def snapshot_material(self) -> dict[str, Any]:
        """Return material derived only from the selected strict path."""
        if self.authorized is not None:
            return dict(self.authorized.authorization_snapshot)

        assert self.refusal_snapshot is not None
        return self.refusal_snapshot.to_material()


class ToolManager:
    """
    Unified tool lifecycle orchestrator.

    Responsibilities:
    - authorize an invocation fully BEFORE the effect syscall
      (:meth:`authorize`)
    - execute a sealed, authorized invocation and finalize its
      confirmation on the effect boundary (:meth:`execute_authorized`)

    Retry orchestration is owned by CognitiveRuntime and must pass
    through SyscallHandler for audit/replay consistency; every attempt
    is re-authorized, so every intent binds its own fresh verdict.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        executor: ToolExecutor,
        *,
        consent_gate: ConsentGate | None = None,
        egress_gate: EgressGate | None = None,
        require_gates: bool = False,
        confirmation_registry: ConfirmationRegistry | None = None,
    ) -> None:
        self.registry = registry
        self.executor = executor
        self._consent_gate = consent_gate
        self._egress_gate = egress_gate
        # F-017/F-018: when True (production profile), a tool declaring
        # required_consent or data_egress is denied if the matching gate
        # is missing, instead of leaving enforcement to the host.
        self._require_gates = require_gates
        self._confirmation_registry = confirmation_registry
        # Campaign 7 Lot 5: once authorization succeeds, ownership of an
        # exception-safe reservation transaction is transferred to the exact
        # minted capability and finalized from its explicit effect state.
        self._confirmation_reservations: dict[str, ConfirmationReservation] = {}
        # Campaign 6 (Lot 3, closes a8 section 10): the manager is the
        # single minter. The claim is exactly-once per executor, so no
        # later caller can obtain the mint from the public graph.
        self._authority = executor.claim_minting_authority()

    # ------------------------------------------------------------------
    # Phase 1: pre-syscall authorization
    # ------------------------------------------------------------------
    def authorize(self, result: Any, ctx: Any) -> ToolAuthorizationOutcome | None:
        """Full pre-effect authorization of the decided tool invocation.

        Static validation happens before confirmation reservation. Every
        operation after a successful reservation runs inside an exception-safe
        transaction: a refusal or exception releases automatically, while only
        a fully constructed manager-owned capability may take ownership.
        """
        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name = getattr(decision, "tool", None)
        if not isinstance(tool_name, str):
            return None

        raw_payload = getattr(decision, "tool_payload", {})
        if raw_payload is None:
            raw_payload = {}

        try:
            frozen_payload = FrozenEffectPayload(raw_payload)
        except (FrozenEffectPayloadError, TypeError, ValueError) as exc:
            return self._refusal_outcome(
                ctx,
                tool_name=tool_name,
                reason="invalid_effect_payload",
                error=ToolInputValidationError(
                    "tool payload cannot be isolated as canonical effect material",
                    details={"exception_type": type(exc).__name__},
                ),
            )

        # Static failures precede reservation and therefore cannot lock a human
        # confirmation.
        tool = self.registry.get(tool_name)
        if tool is None:
            return self._refusal_outcome(
                ctx,
                tool_name=tool_name,
                reason="unknown_tool",
                error=UnknownToolError(f"Unknown tool: {tool_name}"),
            )

        spec = tool.spec
        if spec is not None and spec.input_schema:
            violation = _schema_violation(
                frozen_payload.materialize(),
                spec.input_schema,
            )
            if violation is not None:
                return self._refusal_outcome(
                    ctx,
                    tool_name=tool_name,
                    reason="input_schema_violation",
                    error=ToolInputValidationError(
                        f"tool {tool_name!r} input violates its declared input_schema",
                        details={"schema_path": violation},
                    ),
                )

        stamped = principal_from_context(ctx)
        principal_id = (
            stamped.user_id if stamped is not None else getattr(ctx, "user_id", None)
        )
        tenant_id = stamped.organization_id if stamped is not None else None

        reservation = self._reserve_confirmation_transaction(
            ctx,
            tool_name=tool_name,
            payload=frozen_payload.materialize(),
            principal=principal_id,
            tenant=tenant_id,
        )
        if reservation is None:
            return self._authorize_after_reservation(
                ctx=ctx,
                tool_name=tool_name,
                frozen_payload=frozen_payload,
                spec=spec,
                stamped=stamped,
                principal_id=principal_id,
                tenant_id=tenant_id,
                reservation=None,
            )

        with reservation:
            return self._authorize_after_reservation(
                ctx=ctx,
                tool_name=tool_name,
                frozen_payload=frozen_payload,
                spec=spec,
                stamped=stamped,
                principal_id=principal_id,
                tenant_id=tenant_id,
                reservation=reservation,
            )

    def _authorize_after_reservation(
        self,
        *,
        ctx: Any,
        tool_name: str,
        frozen_payload: FrozenEffectPayload,
        spec: Any,
        stamped: Any,
        principal_id: str | None,
        tenant_id: str | None,
        reservation: ConfirmationReservation | None,
    ) -> ToolAuthorizationOutcome:
        """Construct policy material and mint under reservation protection."""
        authenticated = authenticated_principal_from_context(ctx)
        confirmation = reservation.confirmation if reservation is not None else None
        confirmation_id = (
            confirmation.confirmation_id if confirmation is not None else None
        )

        consent_channel = getattr(ctx, "consent_granted", None)
        if isinstance(consent_channel, (list, tuple)):
            consent_granted = tuple(
                key for key in consent_channel if isinstance(key, str)
            )
        else:
            consent_granted = ()

        # This canonicalization deliberately remains inside the transaction: a
        # custom canonicalizer failure after reservation must release.
        idempotency_key = "idem:" + stable_hash(
            {
                "idempotency_version": 1,
                "tool": tool_name,
                "payload_sha256": payload_commitment(frozen_payload.materialize()),
                "principal": principal_id,
                "tenant": tenant_id,
                "process_id": resolve_process_id(ctx),
            }
        )

        invocation = ToolInvocation(
            tool_name=tool_name,
            payload=frozen_payload,
            process_id=resolve_process_id(ctx),
            user_id=getattr(ctx, "user_id", None),
            risk_score=_resolve_turn_risk(ctx),
            audit_required=spec.audit_required if spec is not None else False,
            principal=stamped.user_id if stamped is not None else None,
            tenant=stamped.organization_id if stamped is not None else None,
            authentication_source=(
                authenticated.authentication_source
                if authenticated is not None
                else None
            ),
            authentication_strength=(
                authenticated.authentication_strength
                if authenticated is not None
                else None
            ),
            service_id=authenticated.service_id if authenticated is not None else None,
            session_id_hash=(
                authenticated.session_id_hash if authenticated is not None else None
            ),
            consent_granted=consent_granted,
            confirmed=confirmation is not None,
            confirmation_id=confirmation_id,
            confirmation_commitment=(
                confirmation.record_commitment if confirmation is not None else None
            ),
            idempotency_key=idempotency_key,
            context=ctx,
        )

        runtime_policy = getattr(ctx, "runtime_policy", None)
        force_tool = runtime_policy.force_tool if runtime_policy is not None else None
        force_execution = (
            runtime_policy.force_execution if runtime_policy is not None else False
        )
        bypass_policy = (
            force_execution and force_tool is not None and tool_name == force_tool
        )

        if bypass_policy:
            policy = ToolAuthorizationDecision(
                allowed=True,
                reason="forced_execution",
            )
        elif (
            self._consent_gate is None
            and self._egress_gate is None
            and not self._require_gates
        ):
            policy = ToolPolicyEvaluator.evaluate(invocation, self.registry)
        else:
            policy = ToolPolicyEvaluator.evaluate(
                invocation,
                self.registry,
                consent_gate=self._consent_gate,
                egress_gate=self._egress_gate,
                require_gates=self._require_gates,
            )

        if not policy.allowed:
            denial = ToolAuthorizationSnapshot(
                tool_name=tool_name,
                allowed=False,
                reason=policy.reason or "tool_policy_denied",
                principal=invocation.principal,
                tenant=invocation.tenant,
                risk_score=invocation.risk_score,
                confirmed=invocation.confirmed,
                confirmation_commitment=invocation.confirmation_commitment,
                authentication_source=invocation.authentication_source,
                authentication_strength=invocation.authentication_strength,
                service_id=invocation.service_id,
                session_id_hash=invocation.session_id_hash,
            )
            return ToolAuthorizationOutcome(
                refusal=ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=ToolAuthorizationError(policy.reason or "tool_policy_denied"),
                    latency_ms=None,
                    effect_boundary=PRE_EFFECT_REFUSAL,
                ),
                refusal_snapshot=denial,
            )

        authorization_snapshot = ToolAuthorizationSnapshot(
            tool_name=tool_name,
            allowed=True,
            reason=policy.reason or "allowed",
            principal=invocation.principal,
            tenant=invocation.tenant,
            risk_score=invocation.risk_score,
            confirmed=invocation.confirmed,
            confirmation_commitment=invocation.confirmation_commitment,
            authentication_source=invocation.authentication_source,
            authentication_strength=invocation.authentication_strength,
            service_id=invocation.service_id,
            session_id_hash=invocation.session_id_hash,
        )
        authorized = self._authority.mint(
            invocation,
            authorization_snapshot.to_material(),
        )
        try:
            outcome = ToolAuthorizationOutcome(authorized=authorized)
            if reservation is not None and confirmation is not None:
                reservation.handoff()
                try:
                    self._confirmation_reservations[authorized.nonce] = reservation
                except Exception:
                    reservation.release_before_effect()
                    self._authority.revoke(authorized)
                    raise
            return outcome
        except Exception:
            self._authority.revoke(authorized)
            raise

    def owns_outcome(self, outcome: ToolAuthorizationOutcome) -> bool:
        """Whether an exact outcome is admissible for this manager.

        Allowed outcomes must carry the exact intact capability registered by
        this manager's private authority. Refusal outcomes have no executable
        capability; their constructor-level invariant is sufficient because
        they can only produce a pre-effect refusal.
        """
        if type(outcome) is not ToolAuthorizationOutcome:
            return False
        if outcome.authorized is None:
            return True
        return self._authority.verifies(outcome.authorized)

    def activate_authorized(
        self,
        authorized: Any,
        *,
        receipt: Any,
        intent_sha256: str,
        run_id: str | None,
        causal_id: str,
    ) -> bool:
        """Activate one minted capability from an exact validated receipt.

        Receipt validation is repeated here as defense in depth: the manager
        will not trust a caller merely because it claims the syscall boundary
        already checked the outbox acknowledgement. Any mismatch aborts the
        capability and releases its reserved confirmation.
        """
        if type(authorized) is not AuthorizedInvocation:
            return False
        if not isinstance(intent_sha256, str) or not intent_sha256:
            self.abort_authorized(authorized)
            return False
        if not isinstance(causal_id, str) or not causal_id:
            self.abort_authorized(authorized)
            return False
        idempotency_key = authorized.invocation.idempotency_key
        if not isinstance(idempotency_key, str) or not idempotency_key:
            self.abort_authorized(authorized)
            return False
        expected_intent = {
            "commitment_sha256": intent_sha256,
            "run_id": run_id,
            "causal_id": causal_id,
            "idempotency_key": idempotency_key,
        }
        if validate_receipt(receipt, expected_intent) is not None:
            self.abort_authorized(authorized)
            return False
        assert isinstance(receipt, AuditReceipt)
        try:
            activation = CapabilityActivationBinding(
                receipt_id=receipt.receipt_id,
                intent_sha256=intent_sha256,
                run_id=run_id,
                causal_id=causal_id,
                idempotency_key=idempotency_key,
                durable_position=receipt.durable_position,
                store_fingerprint=receipt.store_fingerprint,
                committed_at=receipt.committed_at,
            )
        except (TypeError, ValueError):
            self.abort_authorized(authorized)
            return False
        if not self._authority.activate(authorized, activation):
            self.abort_authorized(authorized)
            return False
        return True

    def capability_state(self, authorized: Any) -> CapabilityState | None:
        """Return the lifecycle state of an exact manager-owned capability."""
        if type(authorized) is not AuthorizedInvocation:
            return None
        return self._authority.state_of(authorized)

    def capability_activation(
        self,
        authorized: Any,
    ) -> CapabilityActivationBinding | None:
        """Return the immutable receipt binding of an exact capability."""
        if type(authorized) is not AuthorizedInvocation:
            return None
        return self._authority.activation_of(authorized)

    def abort_authorized(self, authorized: Any) -> bool:
        """Revoke a pre-effect capability and release its reservation."""
        if type(authorized) is not AuthorizedInvocation:
            return False
        state = self._authority.state_of(authorized)
        if state is None or state is CapabilityState.CONSUMED:
            return False
        revoked = self._authority.revoke(authorized)
        if not revoked:
            return False
        self._finalize_authorized_confirmation(authorized, EFFECT_NOT_STARTED)
        return True

    # ------------------------------------------------------------------
    # Phase 2: sealed execution behind the syscall boundary
    # ------------------------------------------------------------------
    def execute_authorized(
        self,
        authorized: Any,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Execute a sealed invocation and finalize from its effect state."""
        try:
            result_exec = self.executor.execute_invocation(authorized, result, ctx)
        except Exception:
            # Executor exceptions that escape its own phase classification are
            # necessarily before a proven effect boundary. Release and preserve
            # the original exception for the syscall boundary to normalize.
            self._finalize_authorized_confirmation(
                authorized,
                EFFECT_NOT_STARTED,
            )
            raise

        boundary: ToolEffectState | str = (
            EFFECT_NOT_STARTED if result_exec is None else result_exec.effect_boundary
        )
        self._finalize_authorized_confirmation(authorized, boundary)
        return result_exec

    # ------------------------------------------------------------------
    # Composition (unit-test and host convenience)
    # ------------------------------------------------------------------
    def run(self, result: Any, ctx: Any) -> ToolResult | None:
        """Authorize then execute, as one call.

        Convenience composition for direct callers (unit tests, simple
        hosts). The governed runtime path does NOT use it: the runtime
        authorizes first, threads the frozen outcome through the
        syscall, and the syscall body executes the sealed capability,
        so the intent always precedes the effect and follows the
        authorization.
        """
        outcome = self.authorize(result, ctx)
        if outcome is None:
            return None
        if outcome.refusal is not None:
            return outcome.refusal
        assert outcome.authorized is not None

        # Compatibility-only local composition. It still obeys the two-phase
        # invariant by persisting an intent in a volatile reference outbox and
        # activating from its exact receipt before execution. Production hosts
        # must use SyscallHandler with their configured durable sink.
        authorized = outcome.authorized
        causal_id = f"tool-manager-run:{authorized.nonce}"
        intent_sha256 = stable_hash(
            {
                "local_tool_run_version": 1,
                "causal_id": causal_id,
                "tool": authorized.invocation.tool_name,
                "payload_sha256": authorized.payload_sha256,
                "idempotency_key": authorized.invocation.idempotency_key,
                "authorization_snapshot": dict(authorized.authorization_snapshot),
            }
        )
        local_intent = {
            "kind": "syscall_intent",
            "syscall": "tool.execute",
            "causal_id": causal_id,
            "process_id": authorized.invocation.process_id or "none",
            "idempotency_key": authorized.invocation.idempotency_key,
            "commitment_sha256": intent_sha256,
        }
        try:
            receipt = InMemoryAuditSink().append(local_intent)
            if not self.activate_authorized(
                authorized,
                receipt=receipt,
                intent_sha256=intent_sha256,
                run_id=None,
                causal_id=causal_id,
            ):
                raise UnauthorizedExecutionError(
                    "the local compatibility outbox could not activate the capability"
                )
            return self.execute_authorized(authorized, result, ctx)
        except Exception:
            # Idempotent: activation failures already abort; sink failures have
            # not yet done so. Either way no pre-effect reservation may leak.
            self.abort_authorized(authorized)
            raise

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _refusal_outcome(
        self,
        ctx: Any,
        *,
        tool_name: str,
        reason: str,
        error: Any,
    ) -> ToolAuthorizationOutcome:
        """Pre-reservation refusal: nothing reserved, nothing released."""
        stamped = principal_from_context(ctx)
        denial = ToolAuthorizationSnapshot(
            tool_name=tool_name,
            allowed=False,
            reason=reason,
            principal=stamped.user_id if stamped is not None else None,
            tenant=stamped.organization_id if stamped is not None else None,
            risk_score=_resolve_turn_risk(ctx),
            confirmed=False,
            confirmation_commitment=None,
        )
        return ToolAuthorizationOutcome(
            refusal=ToolResult(
                tool_name=tool_name,
                success=False,
                error=error,
                latency_ms=None,
                effect_boundary=PRE_EFFECT_REFUSAL,
            ),
            refusal_snapshot=denial,
        )

    def _reserve_confirmation_transaction(
        self,
        ctx: Any,
        *,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None,
    ) -> ConfirmationReservation | None:
        """Reserve through an exception-safe transaction when one is supplied."""
        if self._confirmation_registry is None:
            return None
        carrier = getattr(ctx, "confirmation_result", None)
        confirmation_id = getattr(carrier, "confirmation_id", None)
        if not isinstance(confirmation_id, str):
            return None
        return self._confirmation_registry.reserve_transaction(
            confirmation_id=confirmation_id,
            tool_name=tool_name,
            payload=payload,
            principal=principal,
            tenant=tenant,
        )

    def _finalize_authorized_confirmation(
        self,
        authorized: Any,
        state: ToolEffectState | str,
    ) -> None:
        """Finalize the exact reservation handed to one capability."""
        if type(authorized) is not AuthorizedInvocation:
            return
        reservation = self._confirmation_reservations.pop(authorized.nonce, None)
        if reservation is not None:
            reservation.commit_after_effect(state)
            return

        # No fallback by confirmation id: only the exact capability-owned
        # transaction may finalize a human confirmation.
        return
