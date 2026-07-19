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

from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from arvis.errors.tool_runtime import ToolAuthorizationError
from arvis.tools.authorized_invocation import (
    AuthorizedInvocation,
    InvocationAuthority,
    UnauthorizedExecutionError,
)
from arvis.tools.effect_dispatcher import EffectDispatcher
from arvis.tools.registry import ToolRegistry
from arvis.tools.tool_result import ToolResult
from arvis.tools.tool_schema import schema_violation


def _schema_violation(instance: Any, schema: dict[str, Any]) -> str | None:
    """Backward-compatible private alias for the shared schema validator."""
    return schema_violation(instance, schema)


@dataclass(slots=True)
class _ExecutorSecurityState:
    authority: InvocationAuthority
    minting_claimed: bool = False


_EXECUTOR_SECURITY: WeakKeyDictionary[object, _ExecutorSecurityState] = (
    WeakKeyDictionary()
)


def _executor_security(executor: object) -> _ExecutorSecurityState:
    state = _EXECUTOR_SECURITY.get(executor)
    if state is None:
        raise UnauthorizedExecutionError("executor security state is unavailable")
    return state


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        # D-7, hardened campaign 6 (Lot 3, closes a8 section 10): the
        # single minting authority for this executor is PRIVATE. The a8
        # audit proved a public `authority` let any holder of the
        # executor mint its own capability, bypassing confirmation,
        # policy, manager, syscall and audit. The only handle is
        # _claim_minting_authority(), claimable exactly once by the
        # manager during internal composition.
        _EXECUTOR_SECURITY[self] = _ExecutorSecurityState(
            authority=InvocationAuthority()
        )

    def _claim_minting_authority(self) -> InvocationAuthority:
        """Hand over the minting authority, EXACTLY ONCE (Lot 3).

        Internal composition only. ToolManager calls this at construction;
        once the system is
        composed there is no reachable mint on the public object graph.
        A second claim raises: two components cannot both hold the
        mint, and a later caller cannot obtain it.
        """
        state = _executor_security(self)
        if state.minting_claimed:
            raise UnauthorizedExecutionError(
                "the minting authority of this executor was already "
                "claimed; there is exactly one minter per executor"
            )
        state.minting_claimed = True
        return state.authority

    def claim_minting_authority(self) -> InvocationAuthority:
        """Public mint claims are forbidden; composition owns the authority."""
        raise UnauthorizedExecutionError(
            "minting authority is internal to ToolManager composition"
        )

    def _execute_invocation(
        self,
        authorized: AuthorizedInvocation,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Dispatch one capability through the isolated effect service."""
        state = _executor_security(self)
        return EffectDispatcher(self.registry, state.authority).dispatch(
            authorized,
            result,
            ctx,
        )

    def execute_invocation(
        self,
        authorized: AuthorizedInvocation,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Public capability execution is forbidden outside SyscallHandler."""
        raise UnauthorizedExecutionError(
            "authorized tool execution is internal to the syscall boundary"
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
