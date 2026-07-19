# arvis/tools/confirmation.py
"""Bound tool confirmations, versioned and transactional (campaign 5).

A confirmation is not a boolean: it is a governed record bound to the
exact effect it authorizes. The registry issues records binding a tool
name, the canonical hash of the redacted payload, a principal and an
optional tenant, with an optional expiry.

Campaign 5, Lot 3, two additions on top of the a7 bound record:

- **Explicit format version (D-3).** Every record carries
  ``format_version``. The injective canonicalization of Lot 1 changed
  every ``payload_sha256``, so an a7-era confirmation must never be
  honoured; a record whose version is not the current one is refused at
  reservation. The version is explicit in the record, not inferred from
  a hash mismatch, so the refusal reason is unambiguous.
- **Transactional reserve / commit / release (D-4, closes P1-5).** a7
  consumed the confirmation BEFORE the tool policy was evaluated, so a
  policy denial after resolution burned a legitimate confirmation for
  an effect that never ran. The lifecycle is now two-phase: ``reserve``
  validates every binding and locks the record (single active
  reservation, not deleted); ``commit`` finalizes and removes it once
  the effect has run; ``release`` returns it to the pool if the effect
  is refused before running. A reserved record cannot be reserved
  again, so it is never double-spent, and it is never lost on a
  pre-effect denial.

``consume`` is kept as a convenience (reserve immediately followed by
commit) for callers that authorize and act atomically.

Campaign 6, Lot 4 (closes a8 section 12), two more additions:

- **Unique record commitment.** The proof used to bind the
  confirmation by its payload hash only, so two DISTINCT human
  decisions on the same (tool, payload, principal, tenant) were
  indistinguishable in the commitment. Every record now computes, at
  issue time, ``record_commitment = H(version, nonce, tool,
  payload_sha256, principal, tenant, issued_at, ttl, issuer)`` with a
  fresh unguessable nonce: one human decision, one commitment. The
  manager binds THIS value into the authorization snapshot and the
  effect intent.
- **Mandatory TTL.** Every record now expires:
  ``ttl_seconds`` defaults to ``DEFAULT_CONFIRMATION_TTL_SECONDS`` and
  must be strictly positive; expiry is checked (and expired records
  purged) at reservation. A confirmation is a time-bounded human
  decision, never an eternal token.

The registry is host-provided runtime state. The wall clock enters the
record commitment as issue metadata of the human decision (the value is
computed once at issue and carried as a hash); the monotonic clock
keeps driving expiry. Confirmation ids and nonces are opaque and
unguessable.
"""

from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Literal, Self

from arvis.kernel_core.syscalls.engagement import (
    redact_for_commitment,
    stable_hash,
)
from arvis.tools.tool_result import ToolEffectState, effect_has_started

# Confirmation record format version. Bumped whenever the binding
# material or the payload canonicalization changes; a record of any
# other version is refused at reservation (reason
# confirmation_version_mismatch). Campaign 5 Lot 1 changed the payload
# hash (v2); campaign 6 Lot 0 changed it again through
# canonicalization v2, so that format was 3. Campaign 8 canonicalization
# v3 distinguishes enums from their scalar parents, so format 4 refuses
# every previously issued record instead of silently reinterpreting it.
CONFIRMATION_FORMAT_VERSION = 4

# Default and mandatory expiry (campaign 6, Lot 4): a confirmation is a
# time-bounded human decision. Hosts pass an explicit ttl_seconds for
# stricter or looser windows; it must be strictly positive.
DEFAULT_CONFIRMATION_TTL_SECONDS = 300.0


def payload_commitment(payload: Any) -> str:
    """Injective canonical hash of a redacted tool payload (campaign 5).

    A tool payload is a business object, not a journal envelope: it is
    canonicalized injectively (type-preserving) with content-bearing
    fields redacted to their canonical hash. No volatile stripping is
    applied - the a7 collision where two payloads differing only by a
    business ``id`` produced the same commitment (and let a confirmation
    for record-A authorize record-B) is closed at the root. A
    non-canonicalizable payload raises rather than aliasing.
    """
    return stable_hash(redact_for_commitment(payload))


@dataclass(frozen=True, slots=True)
class ToolConfirmation:
    """A confirmation bound to one exact effect and one human decision.

    ``record_commitment`` (campaign 6, Lot 4) is the unique commitment
    of THIS decision: version, nonce, tool, payload hash, principal,
    tenant, issue time, ttl and issuer. Two decisions on the same
    effect never share it.
    """

    confirmation_id: str
    tool_name: str
    payload_sha256: str
    principal: str | None
    tenant: str | None
    expires_at_monotonic: float
    nonce: str
    issued_at_unix: float
    ttl_seconds: float
    issuer: str | None
    record_commitment: str
    format_version: int = CONFIRMATION_FORMAT_VERSION


@dataclass(slots=True)
class _StoredConfirmation:
    """Registry-internal record with its reservation state."""

    confirmation: ToolConfirmation
    reserved: bool = False


class ConfirmationMismatchError(Exception):
    """A reservation attempt failed a binding or version check.

    Carries an opaque ``reason`` code (never payload content) so the
    caller can distinguish an unknown id, an expired record, a version
    mismatch, a binding mismatch or an already-reserved record without
    inspecting the effect.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class ConfirmationReservation:
    """Exception-safe reservation transaction for one confirmation.

    The registry reserves before constructing the invocation and evaluating
    host callbacks. Unless ownership is explicitly handed off to a minted
    capability, leaving the context releases the record automatically on
    normal refusal and on every exception. After handoff, the manager finalizes
    the reservation from the explicit :class:`ToolEffectState`.
    """

    __slots__ = (
        "_registry",
        "_confirmation",
        "_handed_off",
        "_closed",
        "_effect_state",
    )

    def __init__(
        self,
        registry: ConfirmationRegistry,
        confirmation: ToolConfirmation | None,
    ) -> None:
        self._registry = registry
        self._confirmation = confirmation
        self._handed_off = False
        self._closed = False
        self._effect_state = ToolEffectState.EFFECT_NOT_STARTED

    @property
    def confirmation(self) -> ToolConfirmation | None:
        return self._confirmation

    @property
    def confirmation_id(self) -> str | None:
        if self._confirmation is None:
            return None
        return self._confirmation.confirmation_id

    @property
    def effect_state(self) -> ToolEffectState:
        return self._effect_state

    @property
    def handed_off(self) -> bool:
        return self._handed_off

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        del exc_type, exc, traceback
        if not self._handed_off and not self._closed:
            self.release_before_effect()
        return False

    def handoff(self) -> None:
        """Transfer finalization responsibility to the minted capability."""
        if self._closed:
            raise RuntimeError("a closed confirmation reservation cannot be handed off")
        self._handed_off = True

    def release_before_effect(self) -> bool:
        """Release the record and mark the transaction closed, idempotently."""
        if self._closed:
            return False
        self._effect_state = ToolEffectState.EFFECT_NOT_STARTED
        self._closed = True
        confirmation_id = self.confirmation_id
        if confirmation_id is None:
            return False
        return self._registry.release(confirmation_id=confirmation_id)

    def commit_after_effect(self, state: ToolEffectState | str) -> bool:
        """Finalize from an explicit effect state.

        Proven pre-effect states release. Started, completed, failed and
        unknown states commit conservatively because the external effect may
        already have happened.
        """
        if self._closed:
            return False
        try:
            normalized = ToolEffectState(state)
        except ValueError:
            normalized = ToolEffectState.EFFECT_STATE_UNKNOWN
        self._effect_state = normalized
        self._closed = True
        confirmation_id = self.confirmation_id
        if confirmation_id is None:
            return False
        if effect_has_started(normalized):
            return self._registry.commit(confirmation_id=confirmation_id)
        return self._registry.release(confirmation_id=confirmation_id)


class ConfirmationRegistry:
    """Issues and consumes bound, single-use tool confirmations.

    Not thread-safe by design: the runtime doctrine is one instance per
    request; a host sharing a registry across requests owns its own
    synchronization.
    """

    def __init__(self) -> None:
        self._records: dict[str, _StoredConfirmation] = {}

    def issue(
        self,
        *,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None = None,
        ttl_seconds: float = DEFAULT_CONFIRMATION_TTL_SECONDS,
        issuer: str | None = None,
    ) -> ToolConfirmation:
        """Issue a confirmation bound to (tool, payload, principal, tenant).

        Campaign 6 (Lot 4): the TTL is mandatory and strictly positive
        (a confirmation always expires), and the record computes its
        unique ``record_commitment`` at issue time: two decisions on
        the same effect never share a commitment.
        """
        ttl = float(ttl_seconds)
        if not ttl > 0.0:
            raise ValueError("ttl_seconds must be strictly positive")
        payload_sha256 = payload_commitment(payload)
        nonce = secrets.token_hex(16)
        issued_at_unix = time.time()
        record_commitment = stable_hash(
            {
                "confirmation_record_version": 1,
                "format_version": CONFIRMATION_FORMAT_VERSION,
                "nonce": nonce,
                "tool_name": tool_name,
                "payload_sha256": payload_sha256,
                "principal": principal,
                "tenant": tenant,
                "issued_at_unix": issued_at_unix,
                "ttl_seconds": ttl,
                "issuer": issuer,
            }
        )
        record = ToolConfirmation(
            confirmation_id=uuid.uuid4().hex,
            tool_name=tool_name,
            payload_sha256=payload_sha256,
            principal=principal,
            tenant=tenant,
            expires_at_monotonic=time.monotonic() + ttl,
            nonce=nonce,
            issued_at_unix=issued_at_unix,
            ttl_seconds=ttl,
            issuer=issuer,
            record_commitment=record_commitment,
            format_version=CONFIRMATION_FORMAT_VERSION,
        )
        self._records[record.confirmation_id] = _StoredConfirmation(record)
        return record

    def _match(
        self,
        *,
        confirmation_id: str,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None,
    ) -> tuple[_StoredConfirmation | None, str | None]:
        """Validate every binding; return (record, reason).

        On success returns (stored, None). On failure returns
        (None, reason) with an opaque reason code. Expired records are
        purged here. Never mutates the reservation state.
        """
        stored = self._records.get(confirmation_id)
        if stored is None:
            return None, "unknown_confirmation"
        record = stored.confirmation
        if time.monotonic() > record.expires_at_monotonic:
            # Mandatory TTL (campaign 6, Lot 4): every record expires;
            # an expired one is purged and refused at reservation.
            del self._records[confirmation_id]
            return None, "expired_confirmation"
        if record.format_version != CONFIRMATION_FORMAT_VERSION:
            return None, "confirmation_version_mismatch"
        if record.tool_name != tool_name:
            return None, "tool_mismatch"
        if record.payload_sha256 != payload_commitment(payload):
            return None, "payload_mismatch"
        if record.principal != principal:
            return None, "principal_mismatch"
        if record.tenant != tenant:
            return None, "tenant_mismatch"
        return stored, None

    def reserve(
        self,
        *,
        confirmation_id: str,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None = None,
    ) -> ToolConfirmation | None:
        """Validate and lock a confirmation without removing it (D-4).

        Returns the record and marks it reserved when every binding and
        the format version match and it is not already reserved. Returns
        None on any mismatch; a mismatch never mutates the record, so a
        wrong attempt cannot burn a legitimate confirmation. The
        reservation must be finalized with :meth:`commit` after the
        effect runs, or returned with :meth:`release` if the effect is
        refused before running.
        """
        stored, reason = self._match(
            confirmation_id=confirmation_id,
            tool_name=tool_name,
            payload=payload,
            principal=principal,
            tenant=tenant,
        )
        if stored is None:
            return None
        if stored.reserved:
            # Already reserved: never double-spend.
            return None
        stored.reserved = True
        return stored.confirmation

    def reserve_transaction(
        self,
        *,
        confirmation_id: str,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None = None,
    ) -> ConfirmationReservation:
        """Reserve and return an exception-safe lifecycle transaction."""
        confirmation = self.reserve(
            confirmation_id=confirmation_id,
            tool_name=tool_name,
            payload=payload,
            principal=principal,
            tenant=tenant,
        )
        return ConfirmationReservation(self, confirmation)

    def commit(self, *, confirmation_id: str) -> bool:
        """Finalize a reserved confirmation, removing it (single use).

        Returns True when a reserved record existed and was removed;
        False otherwise (unknown or not reserved). Called after the
        effect has run.
        """
        stored = self._records.get(confirmation_id)
        if stored is None or not stored.reserved:
            return False
        del self._records[confirmation_id]
        return True

    def release(self, *, confirmation_id: str) -> bool:
        """Return a reserved confirmation to the pool (pre-effect refusal).

        Returns True when a reserved record existed and was unlocked;
        False otherwise. Called when the effect is refused AFTER
        reservation but BEFORE it runs, so the legitimate confirmation
        survives for a later, authorized attempt (closes P1-5).
        """
        stored = self._records.get(confirmation_id)
        if stored is None or not stored.reserved:
            return False
        stored.reserved = False
        return True

    def consume(
        self,
        *,
        confirmation_id: str,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None = None,
    ) -> ToolConfirmation | None:
        """Reserve and immediately commit; single use (convenience).

        For callers that authorize and act atomically with no
        intervening step that could refuse the effect. Equivalent to a
        ``reserve`` followed by ``commit`` on success. A mismatch
        returns None and never consumes the record.
        """
        reserved = self.reserve(
            confirmation_id=confirmation_id,
            tool_name=tool_name,
            payload=payload,
            principal=principal,
            tenant=tenant,
        )
        if reserved is None:
            return None
        self.commit(confirmation_id=confirmation_id)
        return reserved

    def pending_count(self) -> int:
        return len(self._records)


__all__ = [
    "CONFIRMATION_FORMAT_VERSION",
    "DEFAULT_CONFIRMATION_TTL_SECONDS",
    "ConfirmationMismatchError",
    "ConfirmationRegistry",
    "ConfirmationReservation",
    "ToolConfirmation",
    "payload_commitment",
]
