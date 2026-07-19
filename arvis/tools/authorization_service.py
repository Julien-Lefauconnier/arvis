"""Typed pre-effect authorization service.

Campaign 7 Lot 9 extracts pure authorization preparation from ``ToolManager``.
The manager keeps ownership of confirmation transactions and capability minting;
this service only builds immutable policy material and returns typed failures.
"""

from __future__ import annotations

from collections.abc import Callable
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
from arvis.errors.base import ArvisError
from arvis.errors.tool_runtime import ToolInputValidationError, UnknownToolError
from arvis.kernel_core.access.identity import (
    authenticated_principal_from_context,
    principal_from_context,
)
from arvis.kernel_core.access.models import (
    UNAUTHENTICATED_PRINCIPAL_ID,
    Principal,
)
from arvis.tools.confirmation import ConfirmationReservation
from arvis.tools.effect_context import AuthorizedEffectContext
from arvis.tools.registry import ToolRegistry
from arvis.tools.runtime.runtime_bindings import resolve_process_id, resolve_run_id
from arvis.tools.spec import ToolSpec
from arvis.tools.tool_schema import schema_violation


@dataclass(frozen=True, slots=True)
class ToolAuthorizationFailure:
    """One fail-closed authorization preparation result."""

    tool_name: str
    reason: str
    error: ArvisError


@dataclass(frozen=True, slots=True)
class PreparedToolAuthorization:
    """Static, immutable inputs required by the transactional phase."""

    tool_name: str
    frozen_payload: FrozenEffectPayload
    spec: ToolSpec | None
    principal: Principal | None
    principal_id: str | None
    tenant_id: str | None


AuthorizationPreparation = PreparedToolAuthorization | ToolAuthorizationFailure | None


def resolve_turn_risk(ctx: Any) -> float:
    """Resolve the strictest risk signal available for the current turn."""
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


class ToolAuthorizationService:
    """Build immutable authorization material without owning capabilities."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        consent_gate: ConsentGate | None,
        egress_gate: EgressGate | None,
        require_gates: bool,
    ) -> None:
        self._registry = registry
        self._consent_gate = consent_gate
        self._egress_gate = egress_gate
        self._require_gates = require_gates

    def prepare(self, result: Any, ctx: Any) -> AuthorizationPreparation:
        """Extract, freeze and statically validate one tool request."""
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
            return ToolAuthorizationFailure(
                tool_name=tool_name,
                reason="invalid_effect_payload",
                error=ToolInputValidationError(
                    "tool payload cannot be isolated as canonical effect material",
                    details={"exception_type": type(exc).__name__},
                ),
            )

        tool = self._registry.get(tool_name)
        if tool is None:
            return ToolAuthorizationFailure(
                tool_name=tool_name,
                reason="unknown_tool",
                error=UnknownToolError(f"Unknown tool: {tool_name}"),
            )

        spec = tool.spec
        if spec is not None and spec.input_schema:
            violation = schema_violation(
                frozen_payload.materialize(),
                spec.input_schema,
            )
            if violation is not None:
                return ToolAuthorizationFailure(
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
        return PreparedToolAuthorization(
            tool_name=tool_name,
            frozen_payload=frozen_payload,
            spec=spec,
            principal=stamped,
            principal_id=principal_id,
            tenant_id=tenant_id,
        )

    def build_invocation(
        self,
        prepared: PreparedToolAuthorization,
        ctx: Any,
        reservation: ConfirmationReservation | None,
        *,
        payload_commitment_fn: Callable[[Any], str],
        stable_hash_fn: Callable[[Any], str],
    ) -> ToolInvocation:
        """Build the one immutable invocation used by policy, mint and effect."""
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

        process_id = resolve_process_id(ctx)
        idempotency_key = "idem:" + stable_hash_fn(
            {
                # Stable across runtime restarts by doctrine: ``run_id`` and
                # session provenance are deliberately excluded. The host may
                # persist and replay this key for the same logical action.
                "idempotency_version": 2,
                "tool": prepared.tool_name,
                "payload_sha256": payload_commitment_fn(
                    prepared.frozen_payload.materialize()
                ),
                "principal": prepared.principal_id,
                "tenant": prepared.tenant_id,
                "service_id": (
                    authenticated.service_id if authenticated is not None else None
                ),
                "process_id": process_id,
            }
        )

        spec = prepared.spec
        principal_id = prepared.principal_id
        if not isinstance(principal_id, str) or not principal_id:
            principal_id = UNAUTHENTICATED_PRINCIPAL_ID
        effect_context = AuthorizedEffectContext(
            principal=principal_id,
            tenant=prepared.tenant_id,
            authentication_source=(
                authenticated.authentication_source
                if authenticated is not None
                else "unattested"
            ),
            authentication_strength=(
                authenticated.authentication_strength
                if authenticated is not None
                else "none"
            ),
            service_id=authenticated.service_id if authenticated is not None else None,
            session_id_hash=(
                authenticated.session_id_hash if authenticated is not None else None
            ),
            process_id=process_id,
            run_id=resolve_run_id(ctx),
        )
        return ToolInvocation(
            tool_name=prepared.tool_name,
            payload=prepared.frozen_payload,
            effect_context=effect_context,
            user_id=getattr(ctx, "user_id", None),
            risk_score=resolve_turn_risk(ctx),
            audit_required=spec.audit_required if spec is not None else False,
            consent_granted=consent_granted,
            confirmed=confirmation is not None,
            confirmation_id=confirmation_id,
            confirmation_commitment=(
                confirmation.record_commitment if confirmation is not None else None
            ),
            idempotency_key=idempotency_key,
        )

    def evaluate(
        self,
        invocation: ToolInvocation,
        ctx: Any,
    ) -> ToolAuthorizationDecision:
        """Evaluate force policy and host gates against the immutable invocation."""
        runtime_policy = getattr(ctx, "runtime_policy", None)
        force_tool = runtime_policy.force_tool if runtime_policy is not None else None
        force_execution = (
            runtime_policy.force_execution if runtime_policy is not None else False
        )
        bypass_policy = (
            force_execution
            and force_tool is not None
            and invocation.tool_name == force_tool
        )
        if bypass_policy:
            return ToolAuthorizationDecision(
                allowed=True,
                reason="forced_execution",
            )
        if (
            self._consent_gate is None
            and self._egress_gate is None
            and not self._require_gates
        ):
            return ToolPolicyEvaluator.evaluate(invocation, self._registry)
        return ToolPolicyEvaluator.evaluate(
            invocation,
            self._registry,
            consent_gate=self._consent_gate,
            egress_gate=self._egress_gate,
            require_gates=self._require_gates,
        )

    @staticmethod
    def snapshot(
        invocation: ToolInvocation,
        decision: ToolAuthorizationDecision,
    ) -> ToolAuthorizationSnapshot:
        """Build the immutable authorization snapshot from one decision."""
        return ToolAuthorizationSnapshot(
            tool_name=invocation.tool_name,
            allowed=decision.allowed,
            reason=decision.reason
            or ("allowed" if decision.allowed else "tool_policy_denied"),
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


__all__ = [
    "AuthorizationPreparation",
    "PreparedToolAuthorization",
    "resolve_turn_risk",
    "ToolAuthorizationFailure",
    "ToolAuthorizationService",
]
