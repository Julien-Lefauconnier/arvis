# arvis/kernel_core/memory/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | tuple["JsonValue", ...] | dict[str, "JsonValue"]
MemoryValue: TypeAlias = JsonValue


@dataclass(frozen=True)
class MemoryRecord:
    """
    Canonical kernel-level memory record.

    This model is intentionally minimal and deterministic.
    It does not encode higher-level memory semantics such as
    long-term policy, retrieval scoring, or cognitive relevance.
    """

    record_id: str
    user_id: str
    namespace: str
    key: str
    value: MemoryValue
    created_at: int
    updated_at: int
    version: int = 1
    status: str = "active"
    tags: tuple[str, ...] = field(default_factory=tuple)

    def identity(self) -> tuple[str, str, str]:
        return (self.user_id, self.namespace, self.key)
