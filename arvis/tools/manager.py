# arvis/tools/manager.py

from typing import Any

from arvis.adapters.tools.authorization import ToolAuthorizationDecision
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
        confirmation = self._resolve_confirmation(
            ctx,
            tool_name=tool_name,
            payload=payload,
            principal=principal_id,
            tenant=tenant_id,
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
            confirmation_id=(
                confirmation.confirmation_id if confirmation is not None else None
            ),
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
            error = ToolAuthorizationError(policy.reason or "tool_policy_denied")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=error,
                latency_ms=None,
            )

        # --- execution ---
        # P1-5-a6: the executor receives the SAME invocation the policy
        # evaluated; nothing is rebuilt between authorization and the
        # tool.
        result_exec = self.executor.execute_invocation(invocation, result, ctx)

        return result_exec

    def _resolve_confirmation(
        self,
        ctx: Any,
        *,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None,
    ) -> ToolConfirmation | None:
        """Consume a bound confirmation for this exact invocation.

        The confirmation id travels on the trusted composition channel
        (``ctx.confirmation_result``), never on request-facing extra.
        Consumption requires the registry record to match the tool, the
        canonical payload hash, the principal and the tenant; it is
        single use. No registry, no id, or any mismatch: the invocation
        stays unconfirmed.
        """
        if self._confirmation_registry is None:
            return None
        carrier = getattr(ctx, "confirmation_result", None)
        confirmation_id = getattr(carrier, "confirmation_id", None)
        if not isinstance(confirmation_id, str):
            return None
        return self._confirmation_registry.consume(
            confirmation_id=confirmation_id,
            tool_name=tool_name,
            payload=payload,
            principal=principal,
            tenant=tenant,
        )
