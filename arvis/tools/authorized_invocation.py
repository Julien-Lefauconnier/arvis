# arvis/tools/authorized_invocation.py
"""Opaque, registered and single-use execution capabilities for tools.

Campaign 6 made the executor's minting authority private and made each
capability single-use, but the capability still transported the
minting secret itself. A holder of one legitimate capability could read
that secret, construct a new :class:`AuthorizedInvocation` with an
attacker-selected nonce and drive a different effect.

Campaign 7, Lot 2 replaces the transported secret with a private
registry owned by :class:`InvocationAuthority`:

- every accepted nonce must have been minted and registered here;
- the registry retains the exact capability and invocation objects;
- a canonical commitment binds the capability format, nonce, complete
  invocation material, authorization snapshot, confirmation commitment
  and idempotency key;
- state transitions are lock-protected and monotone:
  ``MINTED -> ACTIVATED -> CONSUMED`` or ``MINTED/ACTIVATED -> REVOKED``;
- a manually constructed capability, a modified capability, a foreign
  capability, a revoked capability or a replay is refused fail-closed.

The capability contains no authority secret. Possession of the exact
registered object is the grant; the authority is the sole registry and
state-transition owner.
"""

from __future__ import annotations

import copy
import secrets
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from arvis.kernel_core.canonicalization import (
    NonCanonicalizableError,
    canonical_hash,
)

if TYPE_CHECKING:
    from arvis.adapters.tools.invocation import ToolInvocation

CAPABILITY_FORMAT_VERSION = 1

# Immutable empty snapshot for capabilities minted without one (test and
# legacy paths); production minting by the manager always provides the
# real authorization material.
_EMPTY_SNAPSHOT: Mapping[str, Any] = MappingProxyType({})


def _empty_snapshot() -> Mapping[str, Any]:
    """Default factory for the immutable capability snapshot field."""
    return _EMPTY_SNAPSHOT


def _freeze_snapshot(
    authorization_snapshot: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Defensively isolate snapshot material before capability minting."""
    if authorization_snapshot is None:
        return _EMPTY_SNAPSHOT
    snapshot = copy.deepcopy(dict(authorization_snapshot))
    return MappingProxyType(snapshot)


@dataclass(frozen=True, slots=True)
class AuthorizedInvocation:
    """One exact invocation registered by an :class:`InvocationAuthority`.

    The public constructor exists for transport and typing, but
    construction alone grants no authority: execution additionally
    requires this exact object to be present in the consuming
    authority's private registry with a matching commitment and an
    ``ACTIVATED`` state.
    """

    invocation: ToolInvocation
    authorization_snapshot: Mapping[str, Any] = field(default_factory=_empty_snapshot)
    nonce: str = ""
    capability_format_version: int = CAPABILITY_FORMAT_VERSION

    @property
    def payload_sha256(self) -> str:
        """Canonical hash of the exact payload sealed by the invocation."""
        return self.invocation.payload_sha256

    @property
    def canonical_payload_bytes(self) -> bytes:
        """Canonical bytes of the exact payload sealed by the invocation."""
        return self.invocation.canonical_payload_bytes


class CapabilityState(StrEnum):
    """Monotone lifecycle of one registered execution capability."""

    MINTED = "minted"
    ACTIVATED = "activated"
    CONSUMED = "consumed"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class CapabilityRecord:
    """Immutable public-shape metadata retained by the private registry."""

    nonce: str
    commitment_sha256: str
    state: CapabilityState


@dataclass(frozen=True, slots=True)
class _CapabilityEntry:
    """Private registry entry binding metadata to the exact bearer object."""

    capability: AuthorizedInvocation
    invocation: ToolInvocation
    context: Any
    record: CapabilityRecord


def _invocation_commitment(invocation: ToolInvocation) -> str:
    """Commit every immutable field that can select or govern the effect.

    ``context`` is not canonicalized: it is a host runtime carrier and may
    contain services, locks or cycles. Its exact object reference is retained
    and checked separately by the private registry entry. The effect payload
    itself is bound by its canonical bytes and hash.
    """
    return canonical_hash(
        {
            "invocation_format_version": 1,
            "tool_name": invocation.tool_name,
            "canonical_payload_bytes": invocation.canonical_payload_bytes,
            "payload_sha256": invocation.payload_sha256,
            "process_id": invocation.process_id,
            "user_id": invocation.user_id,
            "risk_score": invocation.risk_score,
            "audit_required": invocation.audit_required,
            "principal": invocation.principal,
            "tenant": invocation.tenant,
            "consent_granted": invocation.consent_granted,
            "confirmed": invocation.confirmed,
            "confirmation_id": invocation.confirmation_id,
            "confirmation_commitment": invocation.confirmation_commitment,
            "idempotency_key": invocation.idempotency_key,
        }
    )


def _capability_commitment(capability: AuthorizedInvocation) -> str:
    """Canonical commitment of the complete registered grant."""
    invocation = capability.invocation
    snapshot_commitment = canonical_hash(dict(capability.authorization_snapshot))
    return canonical_hash(
        {
            "capability_format_version": capability.capability_format_version,
            "nonce": capability.nonce,
            "invocation_commitment": _invocation_commitment(invocation),
            "authorization_snapshot_commitment": snapshot_commitment,
            # Kept explicit in addition to the invocation commitment: these
            # are transaction-critical joins and must remain visible in the
            # capability format when the invocation representation evolves.
            "confirmation_commitment": invocation.confirmation_commitment,
            "idempotency_key": invocation.idempotency_key,
        }
    )


class InvocationAuthority:
    """Private minting registry and lifecycle authority for one executor."""

    __slots__ = ("_records", "_lock")

    def __init__(self) -> None:
        self._records: dict[str, _CapabilityEntry] = {}
        self._lock = threading.Lock()

    def mint(
        self,
        invocation: ToolInvocation,
        authorization_snapshot: Mapping[str, Any] | None = None,
    ) -> AuthorizedInvocation:
        """Mint and register a non-executable capability in ``MINTED`` state.

        Registration and nonce allocation are atomic. The returned object
        becomes executable only after :meth:`activate` succeeds.
        """
        snapshot = _freeze_snapshot(authorization_snapshot)

        with self._lock:
            nonce = secrets.token_hex(16)
            while nonce in self._records:
                nonce = secrets.token_hex(16)

            capability = AuthorizedInvocation(
                invocation=invocation,
                authorization_snapshot=snapshot,
                nonce=nonce,
            )
            commitment = _capability_commitment(capability)
            record = CapabilityRecord(
                nonce=nonce,
                commitment_sha256=commitment,
                state=CapabilityState.MINTED,
            )
            self._records[nonce] = _CapabilityEntry(
                capability=capability,
                invocation=invocation,
                context=invocation.context,
                record=record,
            )
            return capability

    def authorize(
        self,
        invocation: ToolInvocation,
        authorization_snapshot: Mapping[str, Any] | None = None,
    ) -> AuthorizedInvocation:
        """Compatibility composition: mint then activate one capability.

        Lot 2 introduces the lifecycle without changing the current
        manager transaction boundary. Campaign 7 Lot 4 will call
        :meth:`mint` before durable intent acceptance and :meth:`activate`
        only after a valid receipt. Until then, this method preserves the
        established manager and test surface while still enforcing the
        private registry and commitment.
        """
        capability = self.mint(invocation, authorization_snapshot)
        if not self.activate(capability):  # pragma: no cover - internal invariant
            raise UnauthorizedExecutionError(
                "a freshly minted capability could not be activated"
            )
        return capability

    def _matching_entry_locked(
        self,
        capability: AuthorizedInvocation,
    ) -> _CapabilityEntry | None:
        """Return the exact intact registry entry; caller holds ``_lock``."""
        nonce = capability.nonce
        if not nonce:
            return None
        entry = self._records.get(nonce)
        if entry is None:
            return None
        if entry.capability is not capability:
            return None
        if entry.invocation is not capability.invocation:
            return None
        if entry.context is not capability.invocation.context:
            return None
        if capability.capability_format_version != CAPABILITY_FORMAT_VERSION:
            return None
        try:
            commitment = _capability_commitment(capability)
        except (NonCanonicalizableError, TypeError, ValueError, OverflowError):
            return None
        if not secrets.compare_digest(
            commitment,
            entry.record.commitment_sha256,
        ):
            return None
        return entry

    def verifies(self, capability: AuthorizedInvocation) -> bool:
        """Whether this authority minted this exact, unmodified object.

        Verification is read-only and deliberately independent from the
        lifecycle state: a consumed or revoked capability remains
        attributable to this authority, but cannot be consumed again.
        """
        if not isinstance(capability, AuthorizedInvocation):
            return False
        with self._lock:
            return self._matching_entry_locked(capability) is not None

    def state_of(self, capability: AuthorizedInvocation) -> CapabilityState | None:
        """Return the lifecycle state of an exact intact capability."""
        if not isinstance(capability, AuthorizedInvocation):
            return None
        with self._lock:
            entry = self._matching_entry_locked(capability)
            return entry.record.state if entry is not None else None

    def activate(self, capability: AuthorizedInvocation) -> bool:
        """Transition an intact capability from ``MINTED`` to ``ACTIVATED``.

        Activation is idempotent for the same already-active capability;
        consumed, revoked, foreign, cloned or modified objects are refused.
        """
        if not isinstance(capability, AuthorizedInvocation):
            return False
        with self._lock:
            entry = self._matching_entry_locked(capability)
            if entry is None:
                return False
            if entry.record.state is CapabilityState.ACTIVATED:
                return True
            if entry.record.state is not CapabilityState.MINTED:
                return False
            updated = replace(entry.record, state=CapabilityState.ACTIVATED)
            self._records[capability.nonce] = replace(entry, record=updated)
            return True

    def revoke(self, capability: AuthorizedInvocation) -> bool:
        """Revoke an unconsumed capability, idempotently and atomically."""
        if not isinstance(capability, AuthorizedInvocation):
            return False
        with self._lock:
            entry = self._matching_entry_locked(capability)
            if entry is None:
                return False
            if entry.record.state is CapabilityState.REVOKED:
                return True
            if entry.record.state is CapabilityState.CONSUMED:
                return False
            updated = replace(entry.record, state=CapabilityState.REVOKED)
            self._records[capability.nonce] = replace(entry, record=updated)
            return True

    def consume(self, capability: AuthorizedInvocation) -> bool:
        """Atomically verify and consume one activated capability.

        Returns ``True`` exactly once. A minted-but-not-activated, revoked,
        consumed, foreign, manually constructed, cloned or modified
        capability returns ``False`` and cannot drive the effect.
        """
        if not isinstance(capability, AuthorizedInvocation):
            return False
        with self._lock:
            entry = self._matching_entry_locked(capability)
            if entry is None or entry.record.state is not CapabilityState.ACTIVATED:
                return False
            updated = replace(entry.record, state=CapabilityState.CONSUMED)
            self._records[capability.nonce] = replace(entry, record=updated)
            return True


class UnauthorizedExecutionError(Exception):
    """Execution was attempted without an active registered capability."""


__all__ = [
    "CAPABILITY_FORMAT_VERSION",
    "AuthorizedInvocation",
    "CapabilityRecord",
    "CapabilityState",
    "InvocationAuthority",
    "UnauthorizedExecutionError",
]
