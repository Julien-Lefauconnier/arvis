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

The registry is host-provided runtime state (wall clock is acceptable
here; it never enters commitment material). Confirmation ids are opaque
and unguessable.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from arvis.kernel_core.syscalls.engagement import (
    redact_for_commitment,
    stable_hash,
)

# Confirmation record format version. Bumped whenever the binding
# material or the payload canonicalization changes; a record of any
# other version is refused at reservation (reason
# confirmation_version_mismatch). Campaign 5 Lot 1 changed the payload
# hash (v2); campaign 6 Lot 0 changed it again through
# canonicalization v2, so this is 3: no a8 (v2) record is honoured.
CONFIRMATION_FORMAT_VERSION = 3


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
    """A confirmation bound to one exact effect."""

    confirmation_id: str
    tool_name: str
    payload_sha256: str
    principal: str | None
    tenant: str | None
    expires_at_monotonic: float | None
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
        ttl_seconds: float | None = None,
    ) -> ToolConfirmation:
        """Issue a confirmation bound to (tool, payload, principal, tenant)."""
        record = ToolConfirmation(
            confirmation_id=uuid.uuid4().hex,
            tool_name=tool_name,
            payload_sha256=payload_commitment(payload),
            principal=principal,
            tenant=tenant,
            expires_at_monotonic=(
                time.monotonic() + float(ttl_seconds)
                if ttl_seconds is not None
                else None
            ),
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
        if (
            record.expires_at_monotonic is not None
            and time.monotonic() > record.expires_at_monotonic
        ):
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
    "ConfirmationMismatchError",
    "ConfirmationRegistry",
    "ToolConfirmation",
    "payload_commitment",
]
