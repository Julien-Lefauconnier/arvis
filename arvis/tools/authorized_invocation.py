# arvis/tools/authorized_invocation.py
"""Opaque, single-use execution capability for tools (campaign 6, Lot 3).

The a7 executor could be driven directly: ``tool_executor`` was a public
attribute on ``CognitiveOS`` and ``execute_invocation`` accepted a bare
``ToolInvocation``. Campaign 5 introduced the capability, but the a8
audit (P1 eleve, section 10) proved the protection incomplete: the
minting authority was PUBLIC on the executor (any holder of the
executor could mint its own capability, bypassing confirmation, policy,
manager, syscall and audit), and a capability could be presented and
executed several times.

Campaign 6 closes both:

- **Private authority.** The executor creates its authority internally
  and never exposes it; the ONLY handle is
  :meth:`ToolExecutor.claim_minting_authority`, claimable EXACTLY ONCE.
  The ToolManager claims it at construction, so once the system is
  composed there is no reachable mint on the public object graph.
- **Single use.** Every minted capability carries an unguessable nonce;
  the executor CONSUMES it at execution (thread-safe, first
  presentation wins). A second presentation of the same capability is
  refused: one authorization, one effect.

This does not pretend to seal a Python process against code that
already runs inside it (the audit says so explicitly); it makes "only
the manager's policy can authorize an effect, once" a property of the
object graph rather than a convention.

Doctrine: the capability is opaque, unforgeable and single-use, like a
grant. The manager is the single authority that mints it; the executor
is the single consumer that honours it. There is no other path to an
effect.
"""

from __future__ import annotations

import secrets
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from arvis.adapters.tools.invocation import ToolInvocation

# Immutable empty snapshot for capabilities minted without one (test and
# legacy paths); production minting by the manager always provides the
# real authorization material.
_EMPTY_SNAPSHOT: Mapping[str, Any] = MappingProxyType({})


def _empty_snapshot() -> Mapping[str, Any]:
    """Default factory for the capability snapshot field.

    Python 3.11 refuses a ``mappingproxy`` instance as a dataclass
    default (3.12 special-cases it as immutable); the factory returns
    the shared immutable proxy either way.
    """
    return _EMPTY_SNAPSHOT


class InvocationAuthority:
    """The single minting authority for authorized invocations.

    One authority is created per executor, privately. It holds an
    unguessable secret, stamps every capability it mints with that
    secret's identity and a fresh single-use nonce, and consumes each
    nonce at execution. The executor honours only the capabilities this
    authority minted AND not yet consumed; a capability from any other
    authority, a forged one, or a replayed one does not pass.
    """

    __slots__ = ("_token", "_consumed", "_lock")

    def __init__(self) -> None:
        self._token = secrets.token_hex(32)
        # Nonces of consumed capabilities. Bounded by the effects of the
        # current runtime instance; runtime lifecycle bounding is a
        # tracked later chantier (a8 section 22).
        self._consumed: set[str] = set()
        self._lock = threading.Lock()

    def authorize(
        self,
        invocation: ToolInvocation,
        authorization_snapshot: Mapping[str, Any] | None = None,
    ) -> AuthorizedInvocation:
        """Mint a single-use capability wrapping an authorized invocation.

        Called by the manager AFTER the policy allowed the invocation.
        The returned capability is the only object the executor accepts,
        and it is consumable exactly once.

        Campaign 6 (Lot 1, closes a8 P0 section 8): the capability
        carries the immutable authorization snapshot of the decision
        that minted it, so the pre-effect intent binds the exact
        verdict from the sealed capability, never a mutable channel.
        The snapshot is frozen at mint time (defensive copy under a
        read-only proxy): pairing a capability with a different
        snapshot is not constructible through this authority.
        """
        snapshot: Mapping[str, Any] = (
            MappingProxyType(dict(authorization_snapshot))
            if authorization_snapshot is not None
            else _EMPTY_SNAPSHOT
        )
        return AuthorizedInvocation(
            _authority_token=self._token,
            invocation=invocation,
            authorization_snapshot=snapshot,
            nonce=secrets.token_hex(16),
        )

    def verifies(self, capability: AuthorizedInvocation) -> bool:
        """True iff this authority minted the capability.

        Constant-time comparison of the stamped token. A capability from
        another authority, or a forged one, does not verify. This is a
        read-only check; it does NOT consume the capability.
        """
        return secrets.compare_digest(capability._authority_token, self._token)

    def consume(self, capability: AuthorizedInvocation) -> bool:
        """Verify AND consume a capability (single use, thread-safe).

        Campaign 6 (Lot 3, closes a8 section 10): the first presentation
        of a minted capability wins; every subsequent presentation of
        the same nonce is refused. Returns True exactly once per minted
        capability; False for a foreign, forged, nonce-less or already
        consumed one.
        """
        if not self.verifies(capability):
            return False
        nonce = capability.nonce
        if not nonce:
            # A capability without a nonce was not minted here.
            return False
        with self._lock:
            if nonce in self._consumed:
                return False
            self._consumed.add(nonce)
        return True


@dataclass(frozen=True, slots=True)
class AuthorizedInvocation:
    """An invocation the manager's policy authorized, usable once.

    Opaque capability: the executor runs a tool only when handed one of
    these, only when its token verifies against the executor's private
    authority, and only on its FIRST presentation (the nonce is
    consumed at execution). Constructing one outside
    :meth:`InvocationAuthority.authorize` yields a token that no
    authority verifies, so a forged capability cannot drive an effect.
    """

    _authority_token: str
    invocation: ToolInvocation
    # Immutable material of the authorization decision that minted this
    # capability (campaign 6, Lot 1); read by the syscall boundary to
    # bind the intent to the exact verdict.
    authorization_snapshot: Mapping[str, Any] = field(default_factory=_empty_snapshot)
    # Single-use marker (campaign 6, Lot 3): stamped at mint, consumed
    # by the executor's authority at execution.
    nonce: str = ""


class UnauthorizedExecutionError(Exception):
    """An execution was attempted without a valid, unused capability.

    Raised when the executor receives a bare invocation, a forged
    capability, a capability minted by a different authority, or a
    capability already consumed (replay). The effect never runs
    (fail-closed).
    """


__all__ = [
    "AuthorizedInvocation",
    "InvocationAuthority",
    "UnauthorizedExecutionError",
]
