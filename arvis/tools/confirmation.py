# arvis/tools/confirmation.py
"""Bound tool confirmations (P1-10-a6, decision D4-d: full object).

A confirmation is not a boolean: it is a governed record bound to the
exact effect it authorizes. The registry issues records binding a tool
name, the canonical hash of the redacted payload, a principal and an
optional tenant, with an optional expiry; consumption is single-use and
requires an exact match on every binding. A mismatched attempt never
consumes the record (a wrong attempt must not burn a legitimate
confirmation), an expired record is purged on sight, and a consumed
record cannot be replayed.

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


class ConfirmationRegistry:
    """Issues and consumes bound, single-use tool confirmations.

    Not thread-safe by design: the runtime doctrine is one instance per
    request; a host sharing a registry across requests owns its own
    synchronization.
    """

    def __init__(self) -> None:
        self._records: dict[str, ToolConfirmation] = {}

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
        )
        self._records[record.confirmation_id] = record
        return record

    def consume(
        self,
        *,
        confirmation_id: str,
        tool_name: str,
        payload: Any,
        principal: str | None,
        tenant: str | None = None,
    ) -> ToolConfirmation | None:
        """Consume a confirmation on exact match; single use.

        Returns the record and removes it when every binding matches
        (tool name, canonical payload hash, principal, tenant) and the
        record has not expired. An unknown id, an expired record (also
        purged), or ANY binding mismatch returns None; a mismatch never
        consumes the record.
        """
        record = self._records.get(confirmation_id)
        if record is None:
            return None
        if (
            record.expires_at_monotonic is not None
            and time.monotonic() > record.expires_at_monotonic
        ):
            del self._records[confirmation_id]
            return None
        if record.tool_name != tool_name:
            return None
        if record.payload_sha256 != payload_commitment(payload):
            return None
        if record.principal != principal:
            return None
        if record.tenant != tenant:
            return None
        del self._records[confirmation_id]
        return record

    def pending_count(self) -> int:
        return len(self._records)


__all__ = ["ConfirmationRegistry", "ToolConfirmation", "payload_commitment"]
