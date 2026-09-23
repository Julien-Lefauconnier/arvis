# arvis/host_api/audit.py

"""Durable audit contracts implemented by a host.

A host owns the persistence technology and its operational durability. ARVIS
defines the generic sink manifest, receipt and protocol that an effect boundary
validates before execution. ``InMemoryAuditSink`` is exported only as the
reference development/test implementation; it is not a durable production
store.

Re-export layer only: every symbol is defined where it lives; this module pins
the import path (see VERSIONING.md, host integration surface).
"""

from arvis.kernel_core.syscalls.audit_sink import (
    AuditReceipt,
    AuditSinkDurabilityClass,
    AuditSinkManifest,
    DurableAuditSink,
    InMemoryAuditSink,
)

__all__ = [
    "AuditReceipt",
    "AuditSinkDurabilityClass",
    "AuditSinkManifest",
    "DurableAuditSink",
    "InMemoryAuditSink",
]
