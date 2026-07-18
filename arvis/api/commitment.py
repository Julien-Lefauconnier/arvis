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

import re
from dataclasses import dataclass
from typing import Any

from arvis.api.ir import IR_VERSION
from arvis.kernel.gate.input_risk import (
    INPUT_RISK_ABSTAIN_THRESHOLD,
    INPUT_RISK_CONFIRM_THRESHOLD,
)

# Redaction primitives live at the kernel boundary
# (arvis/kernel_core/syscalls/engagement.py) since P0-3-a6: the syscall
# handler engages effect parameters before the effect and cannot import
# the API layer. Re-exported here so the public surface is unchanged.
from arvis.kernel_core.host_declaration import component_fingerprint_material
from arvis.kernel_core.syscalls.engagement import (
    REDACTION_POLICY_VERSION,
    redact_for_commitment,
    stable_hash,
    strip_envelope_volatile,
)
from arvis.math.stability.hard_block_policy import HARD_BLOCK_TABLE_VERSION
from arvis.tools.registry import MANIFEST_SCHEMA_VERSION

# v4 (campaign 6): canonicalization v2 changed every hash upstream.
COMMITMENT_VERSION = 4


def syscall_pair_commitments(
    intents: Any,
    results: Any,
) -> list[str]:
    """Ordered per-pair commitments binding each result to ITS intent.

    Campaign 6 (Lot 2, closes a8 section 9.3): the envelope strip drops
    the causal ids from the digest material, so before this, permuting
    two same-syscall results left the journal digest unchanged. Each
    pair commitment is ``H(pair_version, syscall,
    intent_commitment_sha256, canonical redacted result)``, ordered by
    the intent journal order; the journal digest binds the ordered
    list, so any re-pairing changes the digest.

    Total function: an intent without a paired result contributes a
    pair with ``result=None`` (the strict bijection upstream refuses
    such journals before any commitment is composed; the digest stays
    computable for diagnostics).
    """
    intent_entries = intents if isinstance(intents, list) else []
    result_entries = results if isinstance(results, list) else []
    result_map: dict[Any, Any] = {}
    for entry in result_entries:
        if isinstance(entry, dict):
            result_map.setdefault(entry.get("syscall_id"), entry)
    pairs: list[str] = []
    for intent in intent_entries:
        if not isinstance(intent, dict):
            continue
        paired = result_map.get(intent.get("causal_id"))
        pairs.append(
            stable_hash(
                {
                    "pair_version": 1,
                    "syscall": intent.get("syscall"),
                    "intent_commitment_sha256": intent.get("commitment_sha256"),
                    "result": (
                        redact_for_commitment(strip_envelope_volatile(paired))
                        if paired is not None
                        else None
                    ),
                }
            )
        )
    return pairs


def syscall_journal_digest(
    intents: Any,
    results: Any,
) -> str:
    """Digest of the normalized, redacted syscall journals.

    Each journal entry is an envelope: its volatile per-run top-level
    fields (wall-clock, random ids, ticks) are dropped by
    ``strip_envelope_volatile`` at the envelope level only, then
    content-bearing fields are replaced by injective digest markers. A
    business payload nested inside an entry keeps every field. The
    ordered sequence, syscall names, outcomes and error codes remain
    fully bound.

    Campaign 6 (Lot 2): the material additionally binds the ordered
    per-pair commitments (:func:`syscall_pair_commitments`), so a
    permutation of same-syscall results changes the digest even though
    the causal ids are envelope-stripped from the entry material.
    """
    material = {
        "journal_digest_version": 2,
        "intents": redact_for_commitment(
            strip_envelope_volatile(intents if intents is not None else [])
        ),
        "results": redact_for_commitment(
            strip_envelope_volatile(results if results is not None else [])
        ),
        "pair_commitments": syscall_pair_commitments(intents, results),
    }
    return stable_hash(material)


def config_fingerprint(config: Any) -> str:
    """Fingerprint of the effective governance configuration.

    Governance-relevant fields only. Injected components (gates, sinks,
    models) are bound by their declared ``governance_manifest()`` when
    they expose one, so two differently configured instances of the
    same class no longer collide (audit constat 17); a component
    without a manifest falls back to class identity, as in a7. The
    fingerprint commits to WHAT governs, never to payloads.
    """
    adapter_registry = getattr(config, "adapter_registry", None)
    material = {
        "enable_trace": bool(getattr(config, "enable_trace", True)),
        "strict_mode": bool(getattr(config, "strict_mode", False)),
        "runtime_mode": str(getattr(config, "runtime_mode", "")),
        "audit_commitment_policy": str(getattr(config, "audit_commitment_policy", "")),
        "runtime_controls_present": getattr(config, "runtime_controls", None)
        is not None,
        "consent_gate": component_fingerprint_material(
            getattr(config, "consent_gate", None)
        ),
        "egress_gate": component_fingerprint_material(
            getattr(config, "egress_gate", None)
        ),
        "audit_intent_sink": component_fingerprint_material(
            getattr(config, "audit_intent_sink", None)
        ),
        "core_model": component_fingerprint_material(
            getattr(config, "core_model", None)
        ),
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

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class CommitmentInputsValidationError(ValueError):
    """The commitment_inputs block is malformed (P0-2-a6).

    An incomplete or forged proof block must never yield a formally
    valid commitment: validation is strict (exact keys, canonical
    sha256 hex values) and fail-closed.
    """


@dataclass(frozen=True, slots=True)
class CommitmentInputs:
    """Validated non-cognitive commitment components (P0-2-a6)."""

    registry_fingerprint: str
    config_fingerprint: str
    policies_fingerprint: str
    syscall_journal_sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            "registry_fingerprint": self.registry_fingerprint,
            "config_fingerprint": self.config_fingerprint,
            "policies_fingerprint": self.policies_fingerprint,
            "syscall_journal_sha256": self.syscall_journal_sha256,
        }


def validate_commitment_inputs(raw: Any) -> CommitmentInputs:
    """Validate a commitment_inputs block, fail-closed.

    Requirements: a mapping with EXACTLY the four component keys (no
    missing key, no extra key) and canonical lowercase sha256 hex
    values. Anything else raises CommitmentInputsValidationError: an
    absent component must surface as an absent commitment under the
    governed machinery, never compose into a formally valid hash.
    """
    if isinstance(raw, CommitmentInputs):
        raw = raw.to_dict()
    if not isinstance(raw, dict):
        raise CommitmentInputsValidationError("commitment_inputs must be a mapping")
    keys = set(raw.keys())
    missing = COMMITMENT_INPUT_KEYS - keys
    extra = keys - COMMITMENT_INPUT_KEYS
    if missing or extra:
        raise CommitmentInputsValidationError(
            "commitment_inputs keys mismatch: "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )
    values: dict[str, str] = {}
    for key in sorted(COMMITMENT_INPUT_KEYS):
        value = raw[key]
        if not isinstance(value, str) or _SHA256_HEX_RE.fullmatch(value) is None:
            raise CommitmentInputsValidationError(
                f"commitment_inputs[{key!r}] is not a canonical sha256 hex value"
            )
        values[key] = value
    return CommitmentInputs(**values)


def compose_global_commitment(
    *,
    ir_hash: str,
    timeline_commitment: str,
    commitment_inputs: dict[str, Any] | CommitmentInputs,
) -> str:
    """Compose the v2 global commitment from its validated components.

    Explicit named components under canonical JSON: no ambiguous string
    concatenation, and the version is embedded in the hashed material.
    The inputs block is strictly validated first (P0-2-a6): a missing,
    extra or malformed component raises instead of composing over None.
    """
    validated = validate_commitment_inputs(commitment_inputs)
    material = {
        "commitment_version": COMMITMENT_VERSION,
        "ir_hash": ir_hash,
        "timeline_commitment": timeline_commitment,
        **validated.to_dict(),
    }
    return stable_hash(material)


__all__ = [
    "COMMITMENT_INPUT_KEYS",
    "COMMITMENT_VERSION",
    "CommitmentInputs",
    "CommitmentInputsValidationError",
    "validate_commitment_inputs",
    "REDACTION_POLICY_VERSION",
    "compose_global_commitment",
    "config_fingerprint",
    "policies_fingerprint",
    "redact_for_commitment",
    "stable_hash",
    "syscall_journal_digest",
    "syscall_pair_commitments",
]
