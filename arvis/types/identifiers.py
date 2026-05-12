# arvis/types/identifiers.py

from __future__ import annotations

import hashlib
from typing import NewType

EntityID = NewType("EntityID", str)
MemoryKey = NewType("MemoryKey", str)
TimelineID = NewType("TimelineID", str)


def deterministic_id(
    prefix: str,
    *parts: object,
    length: int = 16,
) -> str:
    payload = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}-{digest}"
