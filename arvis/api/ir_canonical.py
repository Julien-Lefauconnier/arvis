# arvis/api/ir_canonical.py

from __future__ import annotations

from typing import Any

from arvis.ir.serialization.canonical_json import (
    canonical_json,
    canonical_json_hash,
)


def canonicalize_ir(ir: dict[str, Any]) -> str:
    """Canonical JSON serialization for ARVIS IR.

    Campaign INTEGRITY (DM-I2): backed by the single canonical JSON
    parameter set (sorted keys, compact separators, ascii-escaped,
    non-finite floats refused), so this public helper produces exactly
    the bytes the result view commits. Before the campaign it
    serialized with ``ensure_ascii=False`` and accepted NaN, so the
    exported tool could not reproduce ``CognitiveResultView.ir_hash``
    on any non-ASCII payload.
    """
    return canonical_json(ir)


def hash_ir(ir: dict[str, Any]) -> str:
    """Stable SHA-256 hash of the canonical IR.

    Reproduces both digests a result carries: ``view.ir_hash`` (over
    the detached IR payload) and ``ir["meta"]["canonical_hash"]``
    (over the IR without that field).
    """
    return canonical_json_hash(ir)
