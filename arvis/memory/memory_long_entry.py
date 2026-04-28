# arvis/memory/memory_long_entry.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MemoryLongType(str, Enum):
    """
    Declarative types of long-term memory.

    Kernel guarantees:
    - no user content
    - classification only
    """

    PREFERENCE = "preference"
    CONTEXT = "context"
    RULE = "rule"
    STYLE = "style"
    CONSTRAINT = "constraint"


@dataclass(frozen=True)
class MemoryLongEntry:
    """
    Kernel representation of long-term memory.

    ZKCS guarantees:
    - content-agnostic
    - immutable
    - temporal traceability
    """

    memory_type: MemoryLongType
    key: str

    created_at: datetime

    source: str
    notes: Optional[str] = None

    # opaque reference (hash / pointer)
    value_ref: Optional[str] = None

    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
