# arvis/tools/authorized_invocation.py
"""Opaque, registered and receipt-activated tool capabilities.

Campaign 7 closes two distinct capability weaknesses in layers:

- Lot 2 removes every transported minting secret and requires each nonce to
  exist in the private :class:`InvocationAuthority` registry.
- Lot 4 separates authorization from execution. A capability is minted in a
  non-executable ``MINTED`` state and becomes executable only after a precise
  intent-acceptance binding has been committed by the syscall outbox.

The lifecycle is monotone and lock-protected::

    MINTED -> ACTIVATED -> CONSUMED
         \\-> REVOKED

Activation binds the exact receipt identity, intent commitment, run identity,
causal identity and durable store position. A capability without that binding,
one activated for another intent or run, a revoked capability, a clone or a
replay is refused fail-closed.
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

INVOCATION_FORMAT_VERSION = 2
CAPABILITY_FORMAT_VERSION = 2
CAPABILITY_ACTIVATION_FORMAT_VERSION = 2

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

    Construction alone grants no authority. Execution additionally requires
    this exact bearer object to be registered, intact, receipt-activated and
    unused in the consuming authority.
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
class CapabilityActivationBinding:
    """Exact outbox acceptance that activates one capability.

    The binding is deliberately independent from the mutable intent envelope.
    It commits the receipt, intent, run and causal identities that were
    validated at the syscall boundary. Empty identifiers are refused; ``run_id``
    may be ``None`` only for direct/non-runtime test compositions where both the
    intent and receipt explicitly carry no run identity.
    """

    receipt_id: str
    intent_sha256: str
    run_id: str | None
    causal_id: str
    durable_position: str
    store_fingerprint: str
    committed_at: str
    idempotency_key: str | None = None
    activation_format_version: int = CAPABILITY_ACTIVATION_FORMAT_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "receipt_id",
            "intent_sha256",
            "causal_id",
            "durable_position",
            "store_fingerprint",
            "committed_at",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.run_id is not None and (
            not isinstance(self.run_id, str) or not self.run_id
        ):
            raise ValueError("run_id must be None or a non-empty string")
        if self.idempotency_key is not None and (
            not isinstance(self.idempotency_key, str) or not self.idempotency_key
        ):
            raise ValueError("idempotency_key must be None or a non-empty string")
        if self.activation_format_version != CAPABILITY_ACTIVATION_FORMAT_VERSION:
            raise ValueError("unsupported capability activation format version")

    @property
    def commitment_sha256(self) -> str:
        """Canonical commitment of the complete activation evidence."""
        return canonical_hash(
            {
                "activation_format_version": self.activation_format_version,
                "receipt_id": self.receipt_id,
                "intent_sha256": self.intent_sha256,
                "run_id": self.run_id,
                "causal_id": self.causal_id,
                "idempotency_key": self.idempotency_key,
                "durable_position": self.durable_position,
                "store_fingerprint": self.store_fingerprint,
                "committed_at": self.committed_at,
            }
        )


@dataclass(frozen=True, slots=True)
class CapabilityRecord:
    """Immutable metadata retained by the private capability registry."""

    nonce: str
    commitment_sha256: str
    state: CapabilityState
    activation_commitment_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class _CapabilityEntry:
    """Private registry entry binding metadata to the exact bearer object."""

    capability: AuthorizedInvocation
    invocation: ToolInvocation
    record: CapabilityRecord
    activation: CapabilityActivationBinding | None = None


def _invocation_commitment(invocation: ToolInvocation) -> str:
    """Commit every immutable field that can select or govern the effect."""
    return canonical_hash(
        {
            "invocation_format_version": INVOCATION_FORMAT_VERSION,
            "tool_name": invocation.tool_name,
            "canonical_payload_bytes": invocation.canonical_payload_bytes,
            "payload_sha256": invocation.payload_sha256,
            "effect_context_commitment": (invocation.effect_context.commitment_sha256),
            "process_id": invocation.process_id,
            "user_id": invocation.user_id,
            "risk_score": invocation.risk_score,
            "audit_required": invocation.audit_required,
            "principal": invocation.principal,
            "tenant": invocation.tenant,
            "authentication_source": invocation.authentication_source,
            "authentication_strength": invocation.authentication_strength,
            "service_id": invocation.service_id,
            "session_id_hash": invocation.session_id_hash,
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
            "effect_context_commitment": (invocation.effect_context.commitment_sha256),
            "authorization_snapshot_commitment": snapshot_commitment,
            "confirmation_commitment": invocation.confirmation_commitment,
            "idempotency_key": invocation.idempotency_key,
        }
    )


class InvocationAuthority:
    """Private minting registry and lifecycle authority for one executor."""

    __slots__ = ("_records", "_receipt_bindings", "_lock")

    def __init__(self) -> None:
        self._records: dict[str, _CapabilityEntry] = {}
        # One durable acknowledgement may activate exactly one capability.
        # The binding is never released: a receipt already accepted cannot be
        # replayed to authorize a second effect, even after revocation.
        self._receipt_bindings: dict[str, str] = {}
        self._lock = threading.Lock()

    def mint(
        self,
        invocation: ToolInvocation,
        authorization_snapshot: Mapping[str, Any] | None = None,
    ) -> AuthorizedInvocation:
        """Mint and register a non-executable capability in ``MINTED`` state."""
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
                record=record,
            )
            return capability

    def authorize(
        self,
        invocation: ToolInvocation,
        authorization_snapshot: Mapping[str, Any] | None = None,
    ) -> AuthorizedInvocation:
        """Compatibility alias for :meth:`mint`.

        Before Campaign 7 Lot 4 this method also activated the capability.
        It intentionally no longer does so: every capability now requires an
        explicit receipt-bound :meth:`activate` transition.
        """
        return self.mint(invocation, authorization_snapshot)

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
        if capability.capability_format_version != CAPABILITY_FORMAT_VERSION:
            return None
        try:
            commitment = _capability_commitment(capability)
        except (NonCanonicalizableError, TypeError, ValueError, OverflowError):
            return None
        if not secrets.compare_digest(commitment, entry.record.commitment_sha256):
            return None
        if entry.activation is None:
            if entry.record.activation_commitment_sha256 is not None:
                return None
        else:
            try:
                activation_commitment = entry.activation.commitment_sha256
            except (NonCanonicalizableError, TypeError, ValueError, OverflowError):
                return None
            recorded = entry.record.activation_commitment_sha256
            if recorded is None or not secrets.compare_digest(
                activation_commitment,
                recorded,
            ):
                return None
        return entry

    def verifies(self, capability: AuthorizedInvocation) -> bool:
        """Whether this authority minted this exact, unmodified object."""
        if type(capability) is not AuthorizedInvocation:
            return False
        with self._lock:
            return self._matching_entry_locked(capability) is not None

    def state_of(self, capability: AuthorizedInvocation) -> CapabilityState | None:
        """Return the lifecycle state of an exact intact capability."""
        if type(capability) is not AuthorizedInvocation:
            return None
        with self._lock:
            entry = self._matching_entry_locked(capability)
            return entry.record.state if entry is not None else None

    def activation_of(
        self,
        capability: AuthorizedInvocation,
    ) -> CapabilityActivationBinding | None:
        """Return the immutable activation binding of an intact capability."""
        if type(capability) is not AuthorizedInvocation:
            return None
        with self._lock:
            entry = self._matching_entry_locked(capability)
            return entry.activation if entry is not None else None

    def activate(
        self,
        capability: AuthorizedInvocation,
        activation: CapabilityActivationBinding,
    ) -> bool:
        """Bind one exact outbox acceptance and activate the capability.

        Repeating the transition with the same binding is idempotent. A
        different receipt, intent, run or causal binding cannot repair or
        re-activate an existing capability.
        """
        if type(capability) is not AuthorizedInvocation:
            return False
        if type(activation) is not CapabilityActivationBinding:
            return False
        try:
            activation_commitment = activation.commitment_sha256
        except (NonCanonicalizableError, TypeError, ValueError, OverflowError):
            return False
        if activation.idempotency_key != capability.invocation.idempotency_key:
            return False

        with self._lock:
            entry = self._matching_entry_locked(capability)
            if entry is None:
                return False
            if entry.record.state is CapabilityState.ACTIVATED:
                recorded = entry.record.activation_commitment_sha256
                bound_nonce = self._receipt_bindings.get(activation.receipt_id)
                return (
                    bound_nonce == capability.nonce
                    and recorded is not None
                    and secrets.compare_digest(activation_commitment, recorded)
                )
            if entry.record.state is not CapabilityState.MINTED:
                return False
            bound_nonce = self._receipt_bindings.get(activation.receipt_id)
            if bound_nonce is not None and bound_nonce != capability.nonce:
                return False
            updated = replace(
                entry.record,
                state=CapabilityState.ACTIVATED,
                activation_commitment_sha256=activation_commitment,
            )
            self._records[capability.nonce] = replace(
                entry,
                record=updated,
                activation=activation,
            )
            self._receipt_bindings[activation.receipt_id] = capability.nonce
            return True

    def revoke(self, capability: AuthorizedInvocation) -> bool:
        """Revoke an unconsumed capability, idempotently and atomically."""
        if type(capability) is not AuthorizedInvocation:
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
        """Atomically verify and consume one receipt-activated capability."""
        if type(capability) is not AuthorizedInvocation:
            return False
        with self._lock:
            entry = self._matching_entry_locked(capability)
            if (
                entry is None
                or entry.record.state is not CapabilityState.ACTIVATED
                or entry.activation is None
                or entry.record.activation_commitment_sha256 is None
            ):
                return False
            updated = replace(entry.record, state=CapabilityState.CONSUMED)
            self._records[capability.nonce] = replace(entry, record=updated)
            return True


class UnauthorizedExecutionError(Exception):
    """Execution was attempted without an active registered capability."""


__all__ = [
    "CAPABILITY_ACTIVATION_FORMAT_VERSION",
    "CAPABILITY_FORMAT_VERSION",
    "INVOCATION_FORMAT_VERSION",
    "AuthorizedInvocation",
    "CapabilityActivationBinding",
    "CapabilityRecord",
    "CapabilityState",
    "UnauthorizedExecutionError",
]
