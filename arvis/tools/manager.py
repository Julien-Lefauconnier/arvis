# arvis/tools/manager.py

from typing import Any

from arvis.adapters.tools.authorization import ToolAuthorizationDecision
from arvis.adapters.tools.authorization_snapshot import ToolAuthorizationSnapshot
from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.errors.tool_runtime import ToolAuthorizationError
from arvis.kernel_core.access.identity import principal_from_context
from arvis.tools.confirmation import ConfirmationRegistry, ToolConfirmation
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.runtime.runtime_bindings import resolve_process_id
from arvis.tools.tool_result import ToolResult


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


class ToolManager:
    """
    Unified tool lifecycle orchestrator.

    Responsibilities:
    - build invocation
    - evaluate policy
    - execute tool
    - execute a single authorized tool invocation

    Retry orchestration is owned by CognitiveRuntime and must pass
    through SyscallHandler for audit/replay consistency.
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

    def run(self, result: Any, ctx: Any) -> ToolResult | None:
        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name = getattr(decision, "tool", None)
        if not isinstance(tool_name, str):
            return None

        payload = getattr(decision, "tool_payload", {}) or {}

        # -----------------------------------------
        # FORCE EXECUTION OVERRIDE (kernel-level)
        # -----------------------------------------
        runtime_policy = getattr(ctx, "runtime_policy", None)

        force_tool = runtime_policy.force_tool if runtime_policy is not None else None

        force_execution = (
            runtime_policy.force_execution if runtime_policy is not None else False
        )

        bypass_policy = (
            force_execution and force_tool is not None and tool_name == force_tool
        )

        # --- build invocation ---
        # F-006-a5: the invocation carries the real turn context.
        # Identity comes from the trusted context channel only (a
        # stamped Principal), never from request-facing extra.
        stamped = principal_from_context(ctx)
        principal_id = (
            stamped.user_id if stamped is not None else getattr(ctx, "user_id", None)
        )
        tenant_id = stamped.organization_id if stamped is not None else None
        # Campaign 5 (D-4, closes P1-5): reserve the confirmation, do
        # NOT consume it yet. The record is validated and locked but
        # stays in the pool, so a policy denial below can release it
        # instead of burning a legitimate confirmation for an effect
        # that never runs. It is committed only after the effect runs.
        confirmation = self._reserve_confirmation(
            ctx,
            tool_name=tool_name,
            payload=payload,
            principal=principal_id,
            tenant=tenant_id,
        )
        confirmation_id = (
            confirmation.confirmation_id if confirmation is not None else None
        )
        invocation = ToolInvocation(
            tool_name=tool_name,
            payload=payload,
            process_id=resolve_process_id(ctx),
            user_id=getattr(ctx, "user_id", None),
            risk_score=_resolve_turn_risk(ctx),
            principal=stamped.user_id if stamped is not None else None,
            tenant=stamped.organization_id if stamped is not None else None,
            confirmed=confirmation is not None,
            confirmation_id=confirmation_id,
            confirmation_commitment=(
                confirmation.payload_sha256 if confirmation is not None else None
            ),
            context=ctx,
        )

        # --- policy evaluation ---
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
            # No gates configured: call the evaluator with its base signature,
            # so any host or test that replaces evaluate() stays compatible.
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
            # Pre-effect refusal: the reserved confirmation is returned
            # to the pool, not burned, so the legitimate effect can be
            # authorized again later (closes P1-5).
            if confirmation_id is not None:
                self._release_confirmation(confirmation_id)
            error = ToolAuthorizationError(policy.reason or "tool_policy_denied")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=error,
                latency_ms=None,
            )

        # Campaign 5 (D-4): the full authorization snapshot travels on
        # the invocation context, so the effect commitment binds not
        # just the parameters but the decision that permitted them
        # (verdict, reason, principal, tenant, risk, confirmation
        # commitment). Two identical effects authorized differently no
        # longer produce the same commitment.
        authorization_snapshot = ToolAuthorizationSnapshot(
            tool_name=tool_name,
            allowed=True,
            reason=policy.reason or "allowed",
            principal=invocation.principal,
            tenant=invocation.tenant,
            risk_score=invocation.risk_score,
            confirmed=invocation.confirmed,
            confirmation_commitment=invocation.confirmation_commitment,
        )
        self._attach_authorization_snapshot(ctx, authorization_snapshot)

        # --- execution ---
        # P1-5-a6: the executor receives the SAME invocation the policy
        # evaluated; nothing is rebuilt between authorization and the
        # tool.
        result_exec = self.executor.execute_invocation(invocation, result, ctx)

        # Campaign 5 (D-4): the effect has run; finalize the reservation
        # (single use). A commit failure is not an effect-refusal path;
        # the effect already happened.
        if confirmation_id is not None:
            self._commit_confirmation(confirmation_id)

        return result_exec

    def _reserve_confirmation(
        self,
        ctx: Any,
        *,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None,
    ) -> ToolConfirmation | None:
        """Reserve a bound confirmation for this exact invocation (D-4).

        The confirmation id travels on the trusted composition channel
        (``ctx.confirmation_result``), never on request-facing extra.
        Reservation validates the tool, the canonical payload hash, the
        principal, the tenant and the format version, and locks the
        record WITHOUT removing it. No registry, no id, or any mismatch:
        the invocation stays unconfirmed and no record is mutated. The
        reservation is finalized by :meth:`_commit_confirmation` after
        the effect runs, or returned by :meth:`_release_confirmation` if
        the effect is refused before running.
        """
        if self._confirmation_registry is None:
            return None
        carrier = getattr(ctx, "confirmation_result", None)
        confirmation_id = getattr(carrier, "confirmation_id", None)
        if not isinstance(confirmation_id, str):
            return None
        return self._confirmation_registry.reserve(
            confirmation_id=confirmation_id,
            tool_name=tool_name,
            payload=payload,
            principal=principal,
            tenant=tenant,
        )

    def _commit_confirmation(self, confirmation_id: str) -> None:
        """Finalize a reserved confirmation after the effect ran."""
        if self._confirmation_registry is None:
            return
        self._confirmation_registry.commit(confirmation_id=confirmation_id)

    def _release_confirmation(self, confirmation_id: str) -> None:
        """Return a reserved confirmation to the pool (pre-effect refusal)."""
        if self._confirmation_registry is None:
            return
        self._confirmation_registry.release(confirmation_id=confirmation_id)

    @staticmethod
    def _attach_authorization_snapshot(
        ctx: Any, snapshot: ToolAuthorizationSnapshot
    ) -> None:
        """Thread the authorization snapshot to the effect commitment.

        Placed on the trusted context extra channel under a stable key;
        the syscall boundary reads it to bind the authorization into the
        effect engagement material. Best-effort: an absent extra channel
        never blocks the authorized effect.
        """
        extra = getattr(ctx, "extra", None)
        if isinstance(extra, dict):
            extra["tool_authorization_snapshot"] = snapshot.to_material()
