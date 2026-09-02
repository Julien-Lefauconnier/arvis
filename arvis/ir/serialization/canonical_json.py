# arvis/ir/serialization/canonical_json.py
"""The single canonical JSON parameter set for IR-shaped payloads.

Campaign INTEGRITY (LOT I2 / DM-I2, audit P0-5, 2026-09-02). Four
encoders used to serialize "canonical" JSON with four different
parameter sets: the public ``hash_ir`` (``ensure_ascii=False``,
NaN silently accepted into non-JSON output), the result view's
``ir_hash`` (``ensure_ascii=True, allow_nan=False``), the decision-id
mint (default separators plus ``default=str``) and the replay witness
serializer (``ensure_ascii=False``). The practical consequence: the
tool exported for integrators could not reproduce the hash the engine
actually committed to.

This module is now the one definition. The parameters are the result
view's, because the view's ``ir_hash`` is the digest results have
been carrying all along: aligning everything else on it means no
committed hash moves.

The object-graph canonicalization of ``arvis/kernel_core/
canonicalization.py`` is a different, versioned layer (commitments
and engagements over Python objects) and deliberately not this.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# One parameter set. sort_keys for order independence; compact
# separators; ensure_ascii so the bytes are unambiguous across
# encodings; allow_nan=False so a non-finite float raises ValueError
# (fail-closed) instead of silently producing non-JSON output.
_CANONICAL_KWARGS: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": True,
    "allow_nan": False,
}


def canonical_json(payload: Any) -> str:
    """Canonical JSON text of a JSON-safe payload.

    Raises ``TypeError`` on non-serializable objects and
    ``ValueError`` on non-finite floats: a payload that cannot be
    canonicalized must fail loudly, never hash approximately.
    """
    return json.dumps(payload, **_CANONICAL_KWARGS)


def canonical_json_bytes(payload: Any) -> bytes:
    """Canonical JSON bytes (UTF-8) of a JSON-safe payload."""
    return canonical_json(payload).encode("utf-8")


def canonical_json_hash(payload: Any) -> str:
    """SHA-256 hex digest of the canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


__all__ = [
    "canonical_json",
    "canonical_json_bytes",
    "canonical_json_hash",
]
