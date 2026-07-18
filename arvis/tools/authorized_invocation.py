# arvis/tools/authorized_invocation.py
"""Opaque execution capability for tools (campaign 5, Lot 6, closes P1-8).

The a7 executor could be driven directly: ``tool_executor`` was a public
attribute on ``CognitiveOS`` and ``execute_invocation`` accepted a bare
``ToolInvocation``, so a caller could run a tool without the manager's
policy ever evaluating it, and ``execute_authorized`` rebuilt a minimal
invocation and ran it, bypassing authorization entirely. The audit
(P1-8) noted this does not create a remote vulnerability, the host being
trusted, but it contradicts the guarantee that an effect cannot
technically run unauthorized.

``AuthorizedInvocation`` is the capability that closes it. It is minted
ONLY by :class:`~arvis.tools.manager.ToolManager` after the policy
authorizes an invocation, wrapping the exact ``ToolInvocation`` the
policy evaluated together with an unguessable token bound to the minting
manager. The executor runs a tool only when handed one of these, and
only when its token verifies against the manager that constructed the
executor's authority. A bare invocation, a forged capability or a
capability from a different manager is refused.

Doctrine: the capability is opaque and unforgeable, like a grant. The
manager is the single authority that mints it; the executor is the
single consumer that honours it. There is no other path to an effect.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arvis.adapters.tools.invocation import ToolInvocation


class InvocationAuthority:
    """The single minting authority for authorized invocations.

    One authority is created per manager. It holds an unguessable secret
    and stamps every capability it mints with that secret's identity.
    The executor is constructed against one authority and honours only
    the capabilities that authority minted; a capability from any other
    authority does not verify.
    """

    __slots__ = ("_token",)

    def __init__(self) -> None:
        self._token = secrets.token_hex(32)

    def authorize(self, invocation: ToolInvocation) -> AuthorizedInvocation:
        """Mint a capability wrapping an authorized invocation.

        Called by the manager AFTER the policy allowed the invocation.
        The returned capability is the only object the executor accepts.
        """
        return AuthorizedInvocation(_authority_token=self._token, invocation=invocation)

    def verifies(self, capability: AuthorizedInvocation) -> bool:
        """True iff this authority minted the capability.

        Constant-time comparison of the stamped token. A capability from
        another authority, or a forged one, does not verify.
        """
        return secrets.compare_digest(capability._authority_token, self._token)


@dataclass(frozen=True, slots=True)
class AuthorizedInvocation:
    """An invocation the manager's policy authorized.

    Opaque capability: the executor runs a tool only when handed one of
    these and only when its token verifies against the executor's
    authority. Constructing one outside :meth:`InvocationAuthority.
    authorize` yields a token that no authority verifies, so a forged
    capability cannot drive an effect.
    """

    _authority_token: str
    invocation: ToolInvocation


class UnauthorizedExecutionError(Exception):
    """An execution was attempted without a verifying capability.

    Raised when the executor receives a bare invocation, a forged
    capability, or a capability minted by a different authority. The
    effect never runs (fail-closed).
    """


__all__ = [
    "AuthorizedInvocation",
    "InvocationAuthority",
    "UnauthorizedExecutionError",
]
