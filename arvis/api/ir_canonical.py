# arvis/api/ir_canonical.py

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize_ir(ir: dict[str, Any]) -> str:
    """
    Canonical JSON serialization for ARVIS IR.

    Guarantees:
    - sorted keys
    - stable separators
    - UTF-8 safe
    """
    return json.dumps(
        ir,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def hash_ir(ir: dict[str, Any]) -> str:
    """
    Stable SHA-256 hash of canonical IR.
    """
    payload = canonicalize_ir(ir).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
