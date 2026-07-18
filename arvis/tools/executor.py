# arvis/tools/executor.py
"""Capability-gated tool executor with effect boundary classification.

Campaign 6 (Lot 1): the authoritative pre-effect validations (tool
existence, input schema) moved to :meth:`ToolManager.authorize`, BEFORE
the confirmation is reserved and BEFORE the pre-effect intent is
recorded. The checks here remain as defense in depth: a capability
should never reach this point with an unknown tool or a violating
payload, but if one does, the refusal is classified as pre-effect so
the confirmation lifecycle never burns a confirmation for an effect
that did not run (closes a8 constat 11).

Every ToolResult carries an ``effect_boundary``: refusals before the
tool body are ``PRE_EFFECT_REFUSAL``; once the body was entered the
boundary is crossed (``EFFECT_COMPLETED``, ``EFFECT_FAILED``) and the
confirmation is considered spent, conservatively including late results
and invalid outputs (the external effect happened).
"""

import time
from typing import Any

import jsonschema

from arvis.errors import normalize_error
from arvis.errors.tool_runtime import (
    ToolAuthorizationError,
    ToolExecutionError,
    ToolInputValidationError,
    ToolOutputValidationError,
    ToolTimeoutError,
    UnknownToolError,
)
from arvis.tools.authorized_invocation import (
    AuthorizedInvocation,
    InvocationAuthority,
    UnauthorizedExecutionError,
)
from arvis.tools.registry import ToolRegistry
from arvis.tools.tool_result import (
    EFFECT_COMPLETED,
    EFFECT_FAILED,
    PRE_EFFECT_REFUSAL,
    ToolResult,
)


def _schema_violation(instance: Any, schema: dict[str, Any]) -> str | None:
    """Validate an instance against a declared JSON schema (F-020).

    Returns a structural path on violation and None when valid. ZK: the
    description carries schema paths only, never the offending values.
    A malformed declared schema cannot validate anything, so it counts
    as a violation on the tool side (fail-closed).
    """
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as exc:
        path = "/".join(str(part) for part in exc.absolute_path)
        return path or "<root>"
    except jsonschema.SchemaError:
        return "<invalid_schema>"
    return None


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        # D-7, hardened campaign 6 (Lot 3, closes a8 section 10): the
        # single minting authority for this executor is PRIVATE. The a8
        # audit proved a public `authority` let any holder of the
        # executor mint its own capability, bypassing confirmation,
        # policy, manager, syscall and audit. The only handle is
        # claim_minting_authority(), claimable exactly once (the
        # manager claims it at construction).
        self._authority = InvocationAuthority()
        self._minting_claimed = False

    def claim_minting_authority(self) -> InvocationAuthority:
        """Hand over the minting authority, EXACTLY ONCE (Lot 3).

        The ToolManager calls this at construction; once the system is
        composed there is no reachable mint on the public object graph.
        A second claim raises: two components cannot both hold the
        mint, and a later caller cannot obtain it.
        """
        if self._minting_claimed:
            raise UnauthorizedExecutionError(
                "the minting authority of this executor was already "
                "claimed; there is exactly one minter per executor"
            )
        self._minting_claimed = True
        return self._authority

    def execute_invocation(
        self,
        authorized: AuthorizedInvocation,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Execute a tool from a verified authorization capability (D-7).

        The executor runs a tool ONLY when handed an
        :class:`AuthorizedInvocation` this executor's authority minted.
        A bare invocation, a forged capability or one from a different
        authority raises :class:`UnauthorizedExecutionError` and the
        effect never runs: there is no path to an effect that the
        manager's policy did not authorize.

        The wrapped ``ToolInvocation`` is the exact object the policy
        evaluated, without reconstruction, so identity, tenant, real
        risk, consent and idempotency are never lost between
        authorization and execution.
        """
        # Campaign 6 (Lot 3, closes a8 section 10): the capability is
        # CONSUMED here, single use. A bare invocation, a forged or
        # foreign capability, or a second presentation of an already
        # executed one is refused and the effect never runs.
        if not isinstance(
            authorized, AuthorizedInvocation
        ) or not self._authority.consume(authorized):
            raise UnauthorizedExecutionError(
                "tool execution requires a verified, unused "
                "AuthorizedInvocation minted by the tool manager's "
                "policy (single use)"
            )
        invocation = authorized.invocation

        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name: str = invocation.tool_name
        tool_payload = invocation.payload or {}

        # legacy payload (kept for compatibility)
        payload_runtime: dict[str, Any] = {
            "decision": decision,
            "context": ctx,
            "tool_payload": tool_payload,
            "invocation": invocation,
        }

        # --- pre-effect phase: nothing external has happened yet ---
        tool = self.registry.get(tool_name)

        if tool is None:
            # Defense in depth: ToolManager.authorize refuses unknown
            # tools before minting; a capability naming one is a
            # host-composition error, still a pre-effect refusal.
            ctx._tool_failure = True
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=UnknownToolError(f"Unknown tool: {tool_name}"),
                latency_ms=None,
                effect_boundary=PRE_EFFECT_REFUSAL,
            )

        spec = tool.spec
        if spec is not None:
            ctx._last_tool_spec = spec

        # F-020, defense in depth (authoritative check moved to
        # ToolManager.authorize): a violating payload never reaches the
        # tool, and the refusal stays pre-effect.
        if spec is not None and spec.input_schema:
            violation = _schema_violation(tool_payload, spec.input_schema)
            if violation is not None:
                ctx._tool_failure = True
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=ToolInputValidationError(
                        f"tool {tool_name!r} input violates its declared input_schema",
                        details={"schema_path": violation},
                    ),
                    latency_ms=None,
                    effect_boundary=PRE_EFFECT_REFUSAL,
                )

        try:
            tool.validate(payload_runtime)
        except Exception as e:
            # The tool's own validation refused the payload BEFORE any
            # external effect: pre-effect refusal, confirmation stays
            # releasable.
            ctx._tool_failure = True
            normalized_error = normalize_error(e)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=ToolExecutionError(
                    normalized_error.message,
                    cause=normalized_error.cause,
                    details={
                        "exception_type": type(e).__name__,
                        "phase": "tool_validate",
                    },
                ),
                latency_ms=None,
                effect_boundary=PRE_EFFECT_REFUSAL,
            )

        # --- effect phase: the boundary is crossed from here on ---
        try:
            start = time.perf_counter()

            if hasattr(tool, "execute_invocation"):
                output = tool.execute_invocation(invocation)
            else:
                output = tool.execute(payload_runtime)

            latency = (time.perf_counter() - start) * 1000

            # F-014: deadline semantics. The tool ran to completion but
            # past its declared budget; the late result is rejected
            # instead of being used, and the violation is surfaced. The
            # effect DID happen: this is a deadline on result
            # acceptance, not an interruption (process isolation is a
            # later chantier), so the boundary is crossed.
            if (
                spec is not None
                and spec.timeout_seconds is not None
                and latency > float(spec.timeout_seconds) * 1000.0
            ):
                ctx._tool_failure = True
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=ToolTimeoutError(
                        f"tool {tool_name!r} exceeded its declared timeout",
                        details={
                            "timeout_seconds": spec.timeout_seconds,
                            "elapsed_ms": round(latency, 3),
                        },
                    ),
                    latency_ms=latency,
                    effect_boundary=EFFECT_COMPLETED,
                )

            # F-020: the declared output schema is validated after the
            # call; an invalid response gets its specific failure status
            # instead of flowing downstream as a success. The effect
            # happened regardless of the invalid output.
            if spec is not None and spec.output_schema:
                violation = _schema_violation(output, spec.output_schema)
                if violation is not None:
                    ctx._tool_failure = True
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        error=ToolOutputValidationError(
                            f"tool {tool_name!r} output violates its "
                            "declared output_schema",
                            details={"schema_path": violation},
                        ),
                        latency_ms=latency,
                        effect_boundary=EFFECT_COMPLETED,
                    )

            return ToolResult(
                tool_name=tool_name,
                success=True,
                output=output,
                error=None,
                latency_ms=latency,
                effect_boundary=EFFECT_COMPLETED,
            )

        except Exception as e:
            # The tool body raised: the effect may have partially
            # happened; the boundary is crossed (conservative).
            ctx._tool_failure = True
            normalized_error = normalize_error(e)
            error = ToolExecutionError(
                normalized_error.message,
                cause=normalized_error.cause,
                details={
                    "exception_type": type(e).__name__,
                },
            )

            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=error,
                latency_ms=None,
                effect_boundary=EFFECT_FAILED,
            )

    def execute(self, arg1: Any, arg2: Any | None = None) -> ToolResult | None:
        """Direct execution is forbidden (D-7).

        There is no unauthorized path to an effect. A tool runs only
        through :meth:`execute_invocation` handed a capability the tool
        manager minted after its policy authorized the invocation. Every
        direct form raises, so neither a tool name nor a rebuilt
        result/ctx can drive an effect that policy never evaluated.
        """
        raise ToolAuthorizationError(
            "direct_tool_execution_forbidden: a tool runs only from an "
            "AuthorizedInvocation minted by the tool manager's policy"
        )
