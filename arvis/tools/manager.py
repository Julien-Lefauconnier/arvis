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
mutable channel. Campaign 7 Lot 8 confines activation and execution to
the private effect-boundary permit claimed by one SyscallHandler; public
manager methods cannot drive an effect.
"""

from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from arvis.adapters.tools.authorization_snapshot import ToolAuthorizationSnapshot
from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.errors.tool_runtime import ToolAuthorizationError
from arvis.kernel_core.access.identity import principal_from_context
from arvis.kernel_core.syscalls.audit_sink import (
    AuditReceipt,
    validate_receipt,
)
from arvis.kernel_core.syscalls.engagement import stable_hash
from arvis.tools.authorization_service import (
    PreparedToolAuthorization,
    ToolAuthorizationFailure,
    ToolAuthorizationService,
    resolve_turn_risk,
)
from arvis.tools.authorized_invocation import (
    AuthorizedInvocation,
    CapabilityActivationBinding,
    CapabilityState,
    InvocationAuthority,
    UnauthorizedExecutionError,
)
from arvis.tools.confirmation import (
    ConfirmationRegistry,
    ConfirmationReservation,
    payload_commitment,
)
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.tool_result import (
    EFFECT_NOT_STARTED,
    PRE_EFFECT_REFUSAL,
    ToolEffectState,
    ToolResult,
)

# Backward-compatible private alias for focused tests.
_resolve_turn_risk = resolve_turn_risk


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

        refusal_snapshot = self.refusal_snapshot
        if refusal_snapshot is None:
            raise RuntimeError("refusal outcome has no authorization snapshot")
        return refusal_snapshot.to_material()


@dataclass(slots=True)
class _ManagerSecurityState:
    authority: InvocationAuthority
    confirmation_reservations: dict[str, ConfirmationReservation]
    effect_boundary_claimed: bool = False


_MANAGER_SECURITY: WeakKeyDictionary[object, _ManagerSecurityState] = (
    WeakKeyDictionary()
)


def _manager_security(manager: object) -> _ManagerSecurityState:
    state = _MANAGER_SECURITY.get(manager)
    if state is None:
        raise UnauthorizedExecutionError("tool manager security state is unavailable")
    return state


class _ToolEffectBoundary:
    """Private controller held only by one SyscallHandler."""

    __slots__ = ("_manager",)

    def __init__(self, manager: "ToolManager") -> None:
        self._manager = manager

    def owns_outcome(self, outcome: ToolAuthorizationOutcome) -> bool:
        return self._manager.owns_outcome(outcome)

    def activate_authorized(
        self,
        authorized: Any,
        *,
        receipt: Any,
        intent_sha256: str,
        run_id: str | None,
        causal_id: str,
    ) -> bool:
        return self._manager._activate_authorized(
            authorized,
            receipt=receipt,
            intent_sha256=intent_sha256,
            run_id=run_id,
            causal_id=causal_id,
        )

    def abort_authorized(self, authorized: Any) -> bool:
        return self._manager._abort_authorized(authorized)

    def execute_authorized(
        self, authorized: Any, result: Any, ctx: Any
    ) -> ToolResult | None:
        return self._manager._execute_authorized(authorized, result, ctx)


class ToolManager:
    """
    Unified tool lifecycle orchestrator.

    Responsibilities:
    - authorize an invocation fully BEFORE the effect syscall
      (:meth:`authorize`)
    - provide private activation/execution operations only to the single
      SyscallHandler that claims the effect boundary

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
        self._authorization_service = ToolAuthorizationService(
            registry,
            consent_gate=consent_gate,
            egress_gate=egress_gate,
            require_gates=require_gates,
        )
        # Security-sensitive state is deliberately absent from the public object
        # graph. The module registry owns the mint and confirmation transactions.
        _MANAGER_SECURITY[self] = _ManagerSecurityState(
            authority=executor._claim_minting_authority(),
            confirmation_reservations={},
        )

    def _claim_effect_boundary(self) -> _ToolEffectBoundary:
        """Hand one private controller to exactly one SyscallHandler."""
        state = _manager_security(self)
        if state.effect_boundary_claimed:
            raise UnauthorizedExecutionError(
                "the tool effect boundary was already claimed by a syscall handler"
            )
        state.effect_boundary_claimed = True
        return _ToolEffectBoundary(self)

    # ------------------------------------------------------------------
    # Phase 1: pre-syscall authorization
    # ------------------------------------------------------------------
    def authorize(self, result: Any, ctx: Any) -> ToolAuthorizationOutcome | None:
        """Authorize one immutable invocation before the effect syscall.

        Static preparation is delegated to :class:`ToolAuthorizationService`.
        The manager retains only the security-sensitive responsibilities:
        confirmation transaction ownership and capability minting.
        """
        prepared = self._authorization_service.prepare(result, ctx)
        if prepared is None:
            return None
        if isinstance(prepared, ToolAuthorizationFailure):
            return self._refusal_outcome(
                ctx,
                tool_name=prepared.tool_name,
                reason=prepared.reason,
                error=prepared.error,
            )

        reservation = self._reserve_confirmation_transaction(
            ctx,
            tool_name=prepared.tool_name,
            payload=prepared.frozen_payload.materialize(),
            principal=prepared.principal_id,
            tenant=prepared.tenant_id,
        )
        if reservation is None:
            return self._complete_authorization(prepared, ctx, None)
        with reservation:
            return self._complete_authorization(prepared, ctx, reservation)

    def _complete_authorization(
        self,
        prepared: PreparedToolAuthorization,
        ctx: Any,
        reservation: ConfirmationReservation | None,
    ) -> ToolAuthorizationOutcome:
        """Evaluate policy and mint while reservation rollback is active."""
        invocation = self._authorization_service.build_invocation(
            prepared,
            ctx,
            reservation,
            payload_commitment_fn=payload_commitment,
            stable_hash_fn=stable_hash,
        )
        policy = self._authorization_service.evaluate(invocation, ctx)
        snapshot = self._authorization_service.snapshot(invocation, policy)

        if not policy.allowed:
            return ToolAuthorizationOutcome(
                refusal=ToolResult(
                    tool_name=prepared.tool_name,
                    success=False,
                    error=ToolAuthorizationError(policy.reason or "tool_policy_denied"),
                    latency_ms=None,
                    effect_boundary=PRE_EFFECT_REFUSAL,
                ),
                refusal_snapshot=snapshot,
            )

        state = _manager_security(self)
        authorized = state.authority.mint(
            invocation,
            snapshot.to_material(),
        )
        try:
            outcome = ToolAuthorizationOutcome(authorized=authorized)
            confirmation = reservation.confirmation if reservation is not None else None
            if reservation is not None and confirmation is not None:
                reservation.handoff()
                try:
                    state.confirmation_reservations[authorized.nonce] = reservation
                except Exception:
                    reservation.release_before_effect()
                    state.authority.revoke(authorized)
                    raise
            return outcome
        except Exception:
            state.authority.revoke(authorized)
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
        return _manager_security(self).authority.verifies(outcome.authorized)

    def _activate_authorized(
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
            self._abort_authorized(authorized)
            return False
        if not isinstance(causal_id, str) or not causal_id:
            self._abort_authorized(authorized)
            return False
        idempotency_key = authorized.invocation.idempotency_key
        if not isinstance(idempotency_key, str) or not idempotency_key:
            self._abort_authorized(authorized)
            return False
        expected_intent = {
            "commitment_sha256": intent_sha256,
            "run_id": run_id,
            "causal_id": causal_id,
            "idempotency_key": idempotency_key,
        }
        if validate_receipt(receipt, expected_intent) is not None:
            self._abort_authorized(authorized)
            return False
        if type(receipt) is not AuditReceipt:
            self._abort_authorized(authorized)
            return False
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
            self._abort_authorized(authorized)
            return False
        if not _manager_security(self).authority.activate(authorized, activation):
            self._abort_authorized(authorized)
            return False
        return True

    def activate_authorized(self, *args: Any, **kwargs: Any) -> bool:
        """Public activation is forbidden; SyscallHandler owns this transition."""
        del args, kwargs
        raise UnauthorizedExecutionError(
            "direct tool effects are forbidden; use SyscallHandler.handle(tool.execute)"
        )

    def abort_authorized(self, *args: Any, **kwargs: Any) -> bool:
        """Public revocation is forbidden outside the syscall transaction."""
        del args, kwargs
        raise UnauthorizedExecutionError(
            "direct tool effects are forbidden; use SyscallHandler.handle(tool.execute)"
        )

    def execute_authorized(self, *args: Any, **kwargs: Any) -> ToolResult | None:
        """Public capability execution is forbidden outside SyscallHandler."""
        del args, kwargs
        raise UnauthorizedExecutionError(
            "direct tool effects are forbidden; use SyscallHandler.handle(tool.execute)"
        )

    def capability_state(self, authorized: Any) -> CapabilityState | None:
        """Return the lifecycle state of an exact manager-owned capability."""
        if type(authorized) is not AuthorizedInvocation:
            return None
        return _manager_security(self).authority.state_of(authorized)

    def capability_activation(
        self,
        authorized: Any,
    ) -> CapabilityActivationBinding | None:
        """Return the immutable receipt binding of an exact capability."""
        if type(authorized) is not AuthorizedInvocation:
            return None
        return _manager_security(self).authority.activation_of(authorized)

    def _abort_authorized(self, authorized: Any) -> bool:
        """Revoke from the private effect controller."""
        if type(authorized) is not AuthorizedInvocation:
            return False
        state = _manager_security(self).authority.state_of(authorized)
        if state is None or state is CapabilityState.CONSUMED:
            return False
        revoked = _manager_security(self).authority.revoke(authorized)
        if not revoked:
            return False
        self._finalize_authorized_confirmation(authorized, EFFECT_NOT_STARTED)
        return True

    # ------------------------------------------------------------------
    # Phase 2: sealed execution behind the syscall boundary
    # ------------------------------------------------------------------
    def _execute_authorized(
        self, authorized: Any, result: Any, ctx: Any
    ) -> ToolResult | None:
        """Execute from the private effect controller."""
        try:
            result_exec = self.executor._execute_invocation(authorized, result, ctx)
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
        """Direct effect composition is not part of the public runtime surface."""
        del result, ctx
        raise UnauthorizedExecutionError(
            "ToolManager.run is not an effect route; use CognitiveOS or "
            "SyscallHandler.handle(tool.execute)"
        )

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
            risk_score=resolve_turn_risk(ctx),
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
        reservation = _manager_security(self).confirmation_reservations.pop(
            authorized.nonce, None
        )
        if reservation is not None:
            reservation.commit_after_effect(state)
            return

        # No fallback by confirmation id: only the exact capability-owned
        # transaction may finalize a human confirmation.
        return
