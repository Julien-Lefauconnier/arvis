# arvis/api/commitment.py
"""Composed run commitment and redaction policy (F-007/F-018-a5).

What arvis did is exactly what arvis can prove it did. The composed
global commitment binds everything that governed a run and everything
the run did: the cognitive IR, the timeline, the syscall journals
(intents and results), the tool-registry manifest fingerprint, the
effective configuration and the active policy tables.

Redaction before hash (ZKCS): content material never enters the hashed
journal in clear. Content-bearing fields are replaced by a canonical
digest marker before serialization, under a versioned policy; widening
the covered field set bumps ``REDACTION_POLICY_VERSION``.

Replay (decision D-a): the non-cognitive components ride in the
exported IR as a ``commitment_inputs`` block, outside the cognitively
hashed sections. A replay recomposes the commitment from those declared
values, never from the replayer's environment, so the property
"identical replay = identical commitment" holds, and a divergent
environment is detectable by comparing the declared block to the local
environment.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from arvis.api.ir import IR_VERSION
from arvis.kernel.gate.input_risk import (
    INPUT_RISK_ABSTAIN_THRESHOLD,
    INPUT_RISK_CONFIRM_THRESHOLD,
)
from arvis.math.stability.hard_block_policy import HARD_BLOCK_TABLE_VERSION
from arvis.tools.registry import MANIFEST_SCHEMA_VERSION

COMMITMENT_VERSION = 2

# Redaction policy v1: fields whose values are content, not structure.
# Their values are replaced by a digest marker before any journal
# material is serialized for hashing.
REDACTION_POLICY_VERSION = 1
_CONTENT_KEYS: frozenset[str] = frozenset(
    {"output", "payload", "result", "content", "text", "prompt"}
)

_REDACTED_MARKER_KEY = "__redacted__"
_TYPE_MARKER_KEY = "__type__"

# Volatile per-run identity and wall-clock fields, dropped from the
# journal material before digesting. The commitment binds WHAT the run
# did (which syscalls, in what order, with what redacted content and
# which outcome codes), never wall-clock instants, random ids or the
# process ordinal: the composed commitment is a deterministic function
# of (input, environment, policies), aligned with deterministic replay.
_VOLATILE_KEYS: frozenset[str] = frozenset(
    {
        "created_at",
        "monotonic_ns",
        "error_id",
        "timestamp",
        "artifact_timestamp",
        "elapsed_ticks",
        "latency_ms",
        "process_id",
        "causal_id",
        "syscall_id",
        "id",
        # Scheduler ticks are monotonic per instance, not per run; the
        # journal's list order already binds the sequence.
        "tick",
        "tick_start",
        "tick_end",
    }
)


def _strip_volatile(obj: Any) -> Any:
    """Drop volatile per-run fields, recursively (digest material only)."""
    if isinstance(obj, dict):
        return {
            k: _strip_volatile(v)
            for k, v in obj.items()
            if not (isinstance(k, str) and k in _VOLATILE_KEYS)
        }
    if isinstance(obj, (list, tuple)):
        return [_strip_volatile(v) for v in obj]
    return obj


def _type_marker(obj: Any) -> dict[str, str]:
    """JSON fallback for non-serializable objects: type identity only.

    Deterministic and ZK-safe: no repr, no address, no content.
    """
    return {_TYPE_MARKER_KEY: type(obj).__qualname__}


def stable_hash(obj: Any) -> str:
    """Deterministic sha256 of the canonical JSON serialization."""
    canonical = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=_type_marker,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _content_digest(value: Any) -> dict[str, Any]:
    """Digest marker replacing a content value under redaction."""
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=_type_marker,
    )
    return {
        _REDACTED_MARKER_KEY: {
            "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "bytes": len(canonical.encode("utf-8")),
            "policy": REDACTION_POLICY_VERSION,
        }
    }


def redact_for_commitment(obj: Any) -> Any:
    """Replace content-bearing fields by digest markers, recursively.

    Structure (keys, nesting, ordering material) is preserved; values
    under the policy's content keys are committed to by hash only.
    """
    if isinstance(obj, dict):
        redacted: dict[str, Any] = {}
        for key, value in obj.items():
            if isinstance(key, str) and key in _CONTENT_KEYS:
                redacted[key] = _content_digest(value)
            else:
                redacted[key] = redact_for_commitment(value)
        return redacted
    if isinstance(obj, (list, tuple)):
        return [redact_for_commitment(v) for v in obj]
    return obj


def syscall_journal_digest(
    intents: Any,
    results: Any,
) -> str:
    """Digest of the normalized, redacted syscall journals.

    Volatile per-run fields are dropped first (see ``_VOLATILE_KEYS``),
    then content-bearing fields are replaced by digest markers. The
    ordered sequence, syscall names, outcomes and error codes remain
    fully bound.
    """
    material = {
        "intents": redact_for_commitment(
            _strip_volatile(intents if intents is not None else [])
        ),
        "results": redact_for_commitment(
            _strip_volatile(results if results is not None else [])
        ),
    }
    return stable_hash(material)


def _qualname_or_none(obj: Any) -> str | None:
    return type(obj).__qualname__ if obj is not None else None


def config_fingerprint(config: Any) -> str:
    """Fingerprint of the effective governance configuration.

    Governance-relevant fields only. Injected objects (gates, sinks,
    models) are represented by presence and type identity, never by
    content: the fingerprint commits to WHAT governs, not to payloads.
    """
    adapter_registry = getattr(config, "adapter_registry", None)
    material = {
        "enable_trace": bool(getattr(config, "enable_trace", True)),
        "strict_mode": bool(getattr(config, "strict_mode", False)),
        "runtime_mode": str(getattr(config, "runtime_mode", "")),
        "audit_commitment_policy": str(getattr(config, "audit_commitment_policy", "")),
        "runtime_controls_present": getattr(config, "runtime_controls", None)
        is not None,
        "consent_gate": _qualname_or_none(getattr(config, "consent_gate", None)),
        "egress_gate": _qualname_or_none(getattr(config, "egress_gate", None)),
        "audit_intent_sink": _qualname_or_none(
            getattr(config, "audit_intent_sink", None)
        ),
        "core_model": _qualname_or_none(getattr(config, "core_model", None)),
        "adapter_keys": (
            sorted(adapter_registry) if isinstance(adapter_registry, dict) else None
        ),
    }
    return stable_hash(material)


def policies_fingerprint() -> str:
    """Fingerprint of the active, versioned policy tables."""
    material = {
        "commitment_version": COMMITMENT_VERSION,
        "hard_block_table_version": HARD_BLOCK_TABLE_VERSION,
        "input_risk_confirm_threshold": INPUT_RISK_CONFIRM_THRESHOLD,
        "input_risk_abstain_threshold": INPUT_RISK_ABSTAIN_THRESHOLD,
        "redaction_policy_version": REDACTION_POLICY_VERSION,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "ir_version": IR_VERSION,
    }
    return stable_hash(material)


COMMITMENT_INPUT_KEYS: frozenset[str] = frozenset(
    {
        "registry_fingerprint",
        "config_fingerprint",
        "policies_fingerprint",
        "syscall_journal_sha256",
    }
)


def compose_global_commitment(
    *,
    ir_hash: str,
    timeline_commitment: str,
    commitment_inputs: dict[str, Any],
) -> str:
    """Compose the v2 global commitment from its components.

    Explicit named components under canonical JSON: no ambiguous string
    concatenation, and the version is embedded in the hashed material.
    """
    material = {
        "commitment_version": COMMITMENT_VERSION,
        "ir_hash": ir_hash,
        "timeline_commitment": timeline_commitment,
        **{key: commitment_inputs.get(key) for key in sorted(COMMITMENT_INPUT_KEYS)},
    }
    return stable_hash(material)


__all__ = [
    "COMMITMENT_INPUT_KEYS",
    "COMMITMENT_VERSION",
    "REDACTION_POLICY_VERSION",
    "compose_global_commitment",
    "config_fingerprint",
    "policies_fingerprint",
    "redact_for_commitment",
    "stable_hash",
    "syscall_journal_digest",
]
