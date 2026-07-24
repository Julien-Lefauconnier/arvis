# arvis/kernel_core/syscalls/audit_sink.py
"""Durable audit sink protocol and receipts (campaign 6, Lot 6).

The a8 audit (section 14) proved the durability of the intent outbox
was declarative: ``audit_intent_sink=lambda intent: None`` satisfied
every control, because ARVIS only verified that a callable existed and
did not raise. Nothing proved the intent had actually been persisted.

This module is the contract that closes it. A durable sink is not a
callable: it is a component that ANSWERS, returning an
:class:`AuditReceipt` binding exactly what was persisted and where:

- ``intent_sha256``: the engagement digest of the persisted intent,
  which MUST equal the intent's own ``commitment_sha256``;
- ``run_id``: the run identity of the intent (campaign 6, Lot 5),
  which MUST equal the intent's journaled ``run_id``: the receipt is
  where the run <-> commitment anchoring lives, by design outside the
  deterministic digest material;
- ``causal_id``: the exact effect occurrence acknowledged by the store,
  preventing one receipt from being replayed across two calls whose
  engagement material happens to be identical;
- ``durable_position``: the store-assigned durable position (an
  offset, a primary key, an LSN);
- ``store_fingerprint``: the identity of the store that accepted it;
- ``receipt_id`` and ``committed_at``: the identity and time of the
  acknowledgement.

For tool effects, ``intent_sha256`` also commits the persisted
``idempotency_key``. The receipt therefore binds that recovery key without
copying it into a second independently mutable receipt field.

The syscall boundary validates every receipt fail-closed: a sink that
returns a malformed receipt, or a receipt binding a DIFFERENT intent,
refuses the effect before it runs. In profiles requiring durability, a
bare callable is refused outright: pretending is no longer accepted.

The receipt is journaled ON the intent entry as envelope material
(stripped from the hashed digest, like the run identity): the
commitment binds WHAT the run did; the receipt binds WHERE that proof
durably lives.

:class:`InMemoryAuditSink` is the reference implementation for tests
and development. It is NOT durable (the name of its store fingerprint
says so); a production host implements real durability behind the same
protocol (for veramem: the PostgreSQL sink, chantier D4-e).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class AuditSinkDurabilityClass(StrEnum):
    """Closed host-declared durability classes."""

    MEMORY = "memory"
    PROCESS = "process"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    DISTRIBUTED_LOG = "distributed_log"


@dataclass(frozen=True, slots=True)
class AuditSinkManifest:
    """Immutable qualification declared by one audit sink implementation."""

    sink_kind: str
    durability_class: AuditSinkDurabilityClass
    transactional: bool
    append_only: bool
    store_fingerprint: str
    implementation_version: str

    def __post_init__(self) -> None:
        for field_name in (
            "sink_kind",
            "store_fingerprint",
            "implementation_version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be a non-empty string")
        if type(self.durability_class) is not AuditSinkDurabilityClass:
            raise TypeError("durability_class must be AuditSinkDurabilityClass")
        if type(self.transactional) is not bool:
            raise TypeError("transactional must be bool")
        if type(self.append_only) is not bool:
            raise TypeError("append_only must be bool")


@dataclass(frozen=True, slots=True)
class AuditReceipt:
    """Acknowledgement that ONE intent was durably persisted."""

    receipt_id: str
    run_id: str | None
    causal_id: str
    intent_sha256: str
    durable_position: str
    store_fingerprint: str
    committed_at: str

    def to_material(self) -> dict[str, Any]:
        """JSON-safe form journaled on the intent entry (envelope)."""
        return {
            "receipt_id": self.receipt_id,
            "run_id": self.run_id,
            "causal_id": self.causal_id,
            "intent_sha256": self.intent_sha256,
            "durable_position": self.durable_position,
            "store_fingerprint": self.store_fingerprint,
            "committed_at": self.committed_at,
        }


@runtime_checkable
class DurableAuditSink(Protocol):
    """A sink that proves persistence instead of declaring it."""

    manifest: AuditSinkManifest

    def append(self, intent: dict[str, Any]) -> AuditReceipt:
        """Persist one intent durably and return its receipt.

        Called synchronously BEFORE the effect runs. Raising, or
        returning an invalid receipt, refuses the effect (fail-closed):
        an intent that cannot be made durable must not be followed by
        its effect.
        """
        ...


def validate_receipt(
    receipt: Any,
    intent: dict[str, Any],
    *,
    manifest: AuditSinkManifest | None = None,
) -> str | None:
    """Fail-closed validation of a sink receipt against ITS intent.

    Returns None when the receipt is well-formed and binds exactly the
    given intent; an opaque reason code otherwise (never payload
    content). The engagement digest and the run identity must match:
    a receipt for a different intent, or for a different run, proves
    nothing about this effect.
    """
    if type(receipt) is not AuditReceipt:
        return "receipt_wrong_type"
    for field_name in (
        "receipt_id",
        "causal_id",
        "durable_position",
        "store_fingerprint",
        "committed_at",
    ):
        value = getattr(receipt, field_name)
        if not isinstance(value, str) or not value:
            return f"receipt_missing_{field_name}"
    if receipt.intent_sha256 != intent.get("commitment_sha256"):
        return "receipt_intent_mismatch"
    if receipt.run_id != intent.get("run_id"):
        return "receipt_run_mismatch"
    if receipt.causal_id != intent.get("causal_id"):
        return "receipt_causal_mismatch"
    if manifest is not None and receipt.store_fingerprint != manifest.store_fingerprint:
        return "receipt_store_fingerprint_mismatch"
    return None


def production_sink_manifest(sink: Any) -> tuple[AuditSinkManifest | None, str | None]:
    """Qualify a sink for a production effect, fail-closed.

    The manifest is a host attestation, not a physical persistence proof. ARVIS
    nevertheless enforces a closed class, transactional acceptance, append-only
    semantics and exact receipt/store identity.
    """
    manifest = getattr(sink, "manifest", None)
    if type(manifest) is not AuditSinkManifest:
        return None, "audit_sink_manifest_required"
    if manifest.durability_class not in {
        AuditSinkDurabilityClass.DATABASE,
        AuditSinkDurabilityClass.DISTRIBUTED_LOG,
    }:
        return None, "audit_sink_durability_class_refused"
    if not manifest.transactional:
        return None, "audit_sink_transaction_required"
    if not manifest.append_only:
        return None, "audit_sink_append_only_required"
    return manifest, None


class InMemoryAuditSink:
    """Reference DurableAuditSink for tests and development.

    NOT durable: entries live in process memory and the store
    fingerprint says ``memory:``. Production hosts implement the same
    protocol over a real durable store; the veramem realization is the
    PostgreSQL sink (D4-e), which persists the intents (outbox) and the
    per-run global commitment, the anchor ``replay_verified``
    authenticates against later.
    """

    def __init__(self) -> None:
        self._store_fingerprint = f"memory:{secrets.token_hex(8)}"
        self.manifest = AuditSinkManifest(
            sink_kind="in_memory",
            durability_class=AuditSinkDurabilityClass.MEMORY,
            transactional=False,
            append_only=True,
            store_fingerprint=self._store_fingerprint,
            implementation_version="1",
        )
        self.entries: list[dict[str, Any]] = []
        self.receipts: list[AuditReceipt] = []

    def append(self, intent: dict[str, Any]) -> AuditReceipt:
        self.entries.append(dict(intent))
        receipt = AuditReceipt(
            receipt_id=secrets.token_hex(16),
            run_id=intent.get("run_id"),
            causal_id=str(intent.get("causal_id", "")),
            intent_sha256=str(intent.get("commitment_sha256", "")),
            durable_position=str(len(self.entries) - 1),
            store_fingerprint=self._store_fingerprint,
            committed_at=datetime.now(UTC).isoformat(),
        )
        self.receipts.append(receipt)
        return receipt


__all__ = [
    "AuditReceipt",
    "AuditSinkDurabilityClass",
    "AuditSinkManifest",
    "DurableAuditSink",
    "InMemoryAuditSink",
    "production_sink_manifest",
    "validate_receipt",
]
