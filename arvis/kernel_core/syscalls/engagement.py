# arvis/kernel_core/syscalls/engagement.py
"""Redaction and pre-effect engagement digest, on the injective core.

Kernel-importable home of the effect-path hash machinery: the syscall
boundary engages the exact parameters of an effect BEFORE it runs, and
the kernel layer cannot import the API layer. ``arvis.api.commitment``
re-exports these names, so the public import surface is unchanged.

Campaign 5, Lot 1 - this module now sits ON TOP of
:mod:`arvis.kernel_core.canonicalization`, the single injective encoder.
Two responsibilities, cleanly separated:

- **Canonicalization** (the core module): "are these two objects the
  same effect?" Type-preserving and injective by contract. A business
  ``id``, a business ``timestamp``, ``bytes`` content and the key type
  are all bound; DELETE record-A and DELETE record-B never coincide.
- **Redaction** (here): "what may cross the ZK boundary?" Content
  values under the policy's content keys are replaced by a digest
  marker. Redaction is lossy by design (that is its purpose), but its
  digest is computed with the injective ``canonical_hash``, so two
  distinct redacted contents still hash differently - the a7 collision
  where ``b"A"`` and ``b"B"`` collapsed in the redaction digest is
  closed.
- **Envelope stripping** (here): per-run technical fields (wall-clock,
  random ids, ticks) are dropped ONLY at the top level of KNOWN journal
  envelope entries, NEVER recursively into business payloads. The a7
  ``_strip_volatile`` that walked into business dicts is gone.

Redaction policy v3 (Lot 1): the covered content-key set is unchanged
from v2, but the digest is now injective (canonical_hash) and the
envelope/business split is enforced. The version bump invalidates a7
hashes by design.
"""

from __future__ import annotations

from typing import Any

from arvis.kernel_core.canonicalization import (
    NonCanonicalizableError,
    canonical_bytes,
    canonical_hash,
)

# Redaction policy v3 (campaign 5): injective digest + envelope split.
# Widening the content set or changing the digest is a version bump.
REDACTION_POLICY_VERSION = 3

_CONTENT_KEYS: frozenset[str] = frozenset(
    {
        "output",
        "payload",
        "result",
        "content",
        "text",
        "prompt",
        # effect parameters carried by tool and LLM paths.
        "tool_payload",
        "arguments",
        "messages",
        "input_data",
    }
)

_REDACTED_MARKER_KEY = "__redacted__"

# Per-run technical fields of a journal ENVELOPE entry. Dropped ONLY at
# the top level of a known envelope (a syscall intent or result entry),
# never recursively: a business payload nested under a content key keeps
# every field. This is the a7 fix - volatile stripping is an envelope
# concern, not a global rewrite.
_ENVELOPE_VOLATILE_KEYS: frozenset[str] = frozenset(
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
        "tick",
        "tick_start",
        "tick_end",
    }
)

# Journal envelopes may nest deeper envelopes under these keys (an
# effect result carries an ``artifact`` envelope; a failed result
# carries an arvis-generated ``error`` envelope with its own wall-clock
# and random ids). Volatile stripping recurses into these declared
# sub-envelopes only. ``error`` is arvis telemetry, never business
# content, so stripping its volatile fields is correct and required for
# the digest to stay deterministic across runs of the same cognition.
_ENVELOPE_CHILD_KEYS: frozenset[str] = frozenset({"artifact", "metadata", "error"})


def stable_hash(obj: Any) -> str:
    """Injective SHA-256 of an effect object (campaign 5).

    Thin alias over :func:`canonical_hash`: the single hash primitive on
    the effect path. Kept under this name for the re-export surface and
    the callers that engaged it in campaigns 3-4.
    """
    return canonical_hash(obj)


def _content_digest(value: Any) -> dict[str, Any]:
    """Digest marker replacing a content value under redaction.

    The digest is the injective ``canonical_hash`` of the value, so two
    distinct contents (including ``b"A"`` vs ``b"B"``, or two business
    ids) never share a redaction marker. ``bytes`` reports the canonical
    byte length so size stays observable.
    """
    raw = canonical_bytes(value)
    return {
        _REDACTED_MARKER_KEY: {
            "sha256": canonical_hash(value),
            "bytes": len(raw),
            "policy": REDACTION_POLICY_VERSION,
        }
    }


def redact_for_commitment(obj: Any) -> Any:
    """Replace content-bearing fields by injective digest markers.

    Structure (keys, nesting, ordering material) is preserved; values
    under the policy's content keys are committed to by their canonical
    hash only. The traversal is structural (dict / list); leaf values
    are left in place for the injective encoder to canonicalize, so no
    type information is lost here.
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


def strip_envelope_volatile(entry: Any) -> Any:
    """Drop per-run technical fields from a KNOWN journal envelope.

    Applied to a single journal entry (intent or result): removes the
    volatile top-level keys and recurses ONLY into declared child
    envelopes (``artifact``, ``metadata``). It never descends into a
    business payload - a value under a content key is returned
    untouched so redaction and canonicalization bind it in full.

    A list of entries is handled element-wise. A non-dict is returned
    as-is (nothing to strip).
    """
    if isinstance(entry, list):
        return [strip_envelope_volatile(e) for e in entry]
    if not isinstance(entry, dict):
        return entry
    out: dict[Any, Any] = {}
    for key, value in entry.items():
        if isinstance(key, str) and key in _ENVELOPE_VOLATILE_KEYS:
            continue
        if isinstance(key, str) and key in _ENVELOPE_CHILD_KEYS:
            # A declared sub-envelope: strip its volatile fields too,
            # but do not treat it as a business payload.
            out[key] = strip_envelope_volatile(value)
        else:
            # Business content and everything else: kept verbatim; the
            # injective encoder and redaction handle it downstream.
            out[key] = value
    return out


# Runtime-binding argument keys excluded from the engagement material.
# These are per-run scheduler bindings (the trusted ctx object, the
# process ordinal), NOT business parameters of the effect. Excluding
# them explicitly by name is the campaign-5 replacement for the a7
# recursive volatile strip: the engagement binds WHAT the effect does,
# and the same effect issued on process ordinal 0 or 1 must engage
# identically. Any other argument (including a business ``id`` or
# ``timestamp``) is bound in full.
_ENGAGEMENT_EXCLUDED_ARG_KEYS: frozenset[str] = frozenset({"ctx", "process_id"})


def effect_engagement_digest(
    *,
    syscall_name: str,
    args: dict[str, Any],
    principal_user_id: str | None,
    principal_organization_id: str | None,
    turn_user_id: str | None,
    authorization_reason_code: str | None,
) -> str:
    """Digest engaging the exact parameters of an effect.

    Computed BEFORE the effect runs and carried by the intent entry:
    binds the syscall, its redacted arguments canonicalized injectively
    (per-run runtime bindings are excluded explicitly by name; identity
    is engaged separately), the principal, the tenant, the turn owner
    and the authorization outcome.

    Campaign 5: the arguments are NOT envelope-stripped - they are a
    business payload, not a journal envelope. Only the runtime bindings
    in ``_ENGAGEMENT_EXCLUDED_ARG_KEYS`` (the trusted ctx object, the
    process ordinal) are dropped, explicitly by name. Two effects whose
    business arguments differ in any operationally significant way (a
    target id, a timestamp, a byte blob) now yield different engagement
    digests, hence different composed commitments. A non-canonicalizable
    argument raises :class:`NonCanonicalizableError` rather than
    aliasing, so a REQUIRED commitment refuses to bind an effect it
    cannot distinguish.
    """
    material_args = {
        k: v for k, v in args.items() if k not in _ENGAGEMENT_EXCLUDED_ARG_KEYS
    }
    material = {
        # engagement_version bumped: the argument material is now the
        # injective canonical form, not the a7 lossy reduction.
        "engagement_version": 2,
        "syscall": syscall_name,
        "effect": "effect",
        "args": redact_for_commitment(material_args),
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
    "NonCanonicalizableError",
    "effect_engagement_digest",
    "redact_for_commitment",
    "stable_hash",
    "strip_envelope_volatile",
]
