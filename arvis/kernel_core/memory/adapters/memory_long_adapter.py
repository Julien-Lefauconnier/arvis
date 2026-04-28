# arvis/kernel_core/memory/adapters/memory_long_adapter.py

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from arvis.kernel_core.memory.models import MemoryRecord
from arvis.memory.memory_long_entry import (
    MemoryLongEntry,
    MemoryLongType,
)


def _to_datetime(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=UTC)


def _infer_memory_type(namespace: str, key: str) -> MemoryLongType:
    """
    Deterministic classification ONLY.

    - No payload access
    - No heuristic ambiguity
    """

    ns = namespace.lower()

    if ns in {"preferences", "pref"}:
        return MemoryLongType.PREFERENCE

    if ns in {"context"}:
        return MemoryLongType.CONTEXT

    if ns in {"rules"}:
        return MemoryLongType.RULE

    if ns in {"style"}:
        return MemoryLongType.STYLE

    if key.startswith("no_"):
        return MemoryLongType.CONSTRAINT

    return MemoryLongType.CONTEXT  # safe default


def _build_value_ref(record: MemoryRecord) -> str:
    """
    Opaque reference.

    No payload leakage.
    Stable + deterministic.
    """
    return f"{record.record_id}:v{record.version}"


def to_memory_long_entry(record: MemoryRecord) -> MemoryLongEntry | None:
    """
    Kernel → cognition adapter (ZKCS compliant)
    """

    if record.status != "active":
        return None

    return MemoryLongEntry(
        memory_type=_infer_memory_type(record.namespace, record.key),
        key=record.key,
        created_at=_to_datetime(record.created_at),
        source="kernel_memory",
        notes=None,
        value_ref=_build_value_ref(record),
        expires_at=None,
        revoked_at=None,
    )


def to_memory_long_entries(
    records: Iterable[MemoryRecord],
) -> list[MemoryLongEntry]:
    entries: list[MemoryLongEntry] = []

    for record in records:
        entry = to_memory_long_entry(record)
        if entry is not None:
            entries.append(entry)

    return entries
