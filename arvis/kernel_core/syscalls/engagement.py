# arvis/kernel_core/syscalls/engagement.py
"""Redaction primitives and pre-effect engagement digest (P0-3-a6).

Kernel-importable home of the redaction machinery introduced with the
composed commitment (campaign 3): the syscall boundary needs it to
engage the exact parameters of an effect BEFORE the effect runs, and
the kernel layer cannot import the API layer. `arvis.api.commitment`
re-exports these names, so the public import surface is unchanged.

Redaction policy v2 widens the covered content field set to tool and
LLM payloads (`tool_payload`, `arguments`, `messages`, `input_data`):
the engagement digest binds an effect's real parameters through their
canonical hashes, never their content (ZKCS).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from typing import Any

# Redaction policy v2: fields whose values are content, not structure.
# Their values are replaced by a digest marker before any journal or
# engagement material is serialized for hashing. Widening this set is a
# policy version bump.
REDACTION_POLICY_VERSION = 2
_CONTENT_KEYS: frozenset[str] = frozenset(
    {
        "output",
        "payload",
        "result",
        "content",
        "text",
        "prompt",
        # v2 (P0-3-a6): effect parameters carried by tool and LLM paths.
        "tool_payload",
        "arguments",
        "messages",
        "input_data",
    }
)

_REDACTED_MARKER_KEY = "__redacted__"
_TYPE_MARKER_KEY = "__type__"

# Volatile per-run identity and wall-clock fields, dropped from digest
# material. The commitment binds WHAT the run did (which syscalls, in
# what order, with what redacted content and which outcome codes),
# never wall-clock instants, random ids or the process ordinal: digests
# are deterministic functions of (input, environment, policies).
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

# Depth cap for object materialization: beyond it, type identity only.
_DEEP_MATERIAL_MAX_DEPTH = 6


def _type_marker(obj: Any) -> dict[str, str]:
    """JSON fallback for non-serializable objects: type identity only.

    Deterministic and ZK-safe: no repr, no address, no content.
    """
    return {_TYPE_MARKER_KEY: type(obj).__qualname__}


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


def deep_material(obj: Any, *, _depth: int = 0, _seen: set[int] | None = None) -> Any:
    """Deterministic, content-preserving materialization of objects.

    Unlike the type-only fallback, this walks object attributes (via
    ``__dict__`` or dataclass fields) so an effect's real parameters
    stay distinguishable in the engagement digest (P0-3-a6: DELETE A
    and DELETE B must not collapse into the same hash). Depth-capped
    and cycle-guarded; beyond the cap or on a cycle, type identity
    only. No reprs, no addresses: deterministic across instances.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if _depth >= _DEEP_MATERIAL_MAX_DEPTH:
        return _type_marker(obj)
    seen = _seen if _seen is not None else set()
    if isinstance(obj, dict):
        return {
            str(k): deep_material(v, _depth=_depth + 1, _seen=seen)
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        return [deep_material(v, _depth=_depth + 1, _seen=seen) for v in obj]
    identity = id(obj)
    if identity in seen:
        return _type_marker(obj)
    seen.add(identity)
    try:
        if is_dataclass(obj) and not isinstance(obj, type):
            attrs = {f.name: getattr(obj, f.name, None) for f in fields(obj)}
        else:
            attrs = vars(obj)
    except TypeError:
        return _type_marker(obj)
    return {
        _TYPE_MARKER_KEY: type(obj).__qualname__,
        "fields": {
            str(k): deep_material(v, _depth=_depth + 1, _seen=seen)
            for k, v in attrs.items()
            if not str(k).startswith("_")
        },
    }


def effect_engagement_digest(
    *,
    syscall_name: str,
    args: dict[str, Any],
    principal_user_id: str | None,
    principal_organization_id: str | None,
    turn_user_id: str | None,
    authorization_reason_code: str | None,
) -> str:
    """Digest engaging the exact parameters of an effect (P0-3-a6).

    Computed BEFORE the effect runs and carried by the intent entry:
    binds the syscall, its materialized redacted arguments (the trusted
    ``ctx`` object is excluded; identity is engaged explicitly), the
    principal, the tenant, the turn owner and the authorization
    outcome. Two effects with different parameters and identical
    results yield different engagement digests, hence different
    composed commitments.
    """
    material_args = {k: v for k, v in args.items() if k != "ctx"}
    material = {
        "engagement_version": 1,
        "syscall": syscall_name,
        "effect": "effect",
        "args": redact_for_commitment(_strip_volatile(deep_material(material_args))),
        "principal_user_id": principal_user_id,
        "principal_organization_id": principal_organization_id,
        "turn_user_id": turn_user_id,
        "authorization": {
            "allowed": True,
            "reason_code": authorization_reason_code,
        },
    }
    return stable_hash(material)


__all__ = [
    "REDACTION_POLICY_VERSION",
    "deep_material",
    "effect_engagement_digest",
    "redact_for_commitment",
    "stable_hash",
]
