# arvis/kernel_core/syscalls/intent_result_bijection.py
"""Strict intent/result bijection for the syscall journals (campaign 5).

Every effect syscall journals an intent BEFORE it runs (carrying the
pre-effect engagement digest) and a result AFTER it runs. The composed
commitment may only bind the journals when they form an exact one-to-one
correspondence: one intent and one result per effect, same syscall, same
causal id, no duplicates, no orphans.

The a7 check (audit P1-6) verified only that each intent's causal id
appeared somewhere in the set of journaled result ids. It missed:

- **duplicate intents**: two intents at one causal id (one effect, two
  engagements): the set membership check passed.
- **orphan results**: a journaled result with no matching intent (an
  effect that ran with no pre-effect engagement): never inspected.
- **syscall mismatch**: an intent and a result at the same causal id
  but for different syscalls: the names were never compared.
- **cardinality**: more than one result per causal id.

The a8 audit (section 9) then proved the correspondence was still
metadata-only: two same-syscall results could be permuted together with
their causal ids and the check passed, because no result carried the
engagement digest of ITS intent. Campaign 6 (Lot 2) closes it: every
intent must carry ``commitment_sha256`` and every paired result must
carry the EQUAL ``intent_commitment_sha256`` (stamped single-use by the
handler at journal time). This result closes this intent, provably; a
permutation is a commitment mismatch.

This module rebuilds strict maps keyed on the causal id, binds the
syscall name and the exact intent commitment, and requires exact 1:1
cardinality. Any deviation yields a structured, opaque reason (no
payload content), so the caller refuses the commitment as
``audit_incomplete`` (REQUIRED refuses the public result, DEGRADED
flags) instead of pretending an unprovable effect was proved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BijectionResult:
    """Outcome of the strict intent/result bijection check.

    ``ok`` is True only for an exact one-to-one correspondence.
    Otherwise ``reason`` is an opaque code (never payload content) and
    ``detail`` names the offending causal id when one applies, for the
    audit trail.
    """

    ok: bool
    reason: str | None = None
    detail: str | None = None

    @classmethod
    def success(cls) -> BijectionResult:
        return cls(ok=True)

    @classmethod
    def failure(cls, reason: str, detail: str | None = None) -> BijectionResult:
        return cls(ok=False, reason=reason, detail=detail)


def _index_by_causal_id(
    entries: list[Any], *, id_key: str
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Map causal id -> entry, refusing duplicates and malformed entries.

    Returns (mapping, reason). ``reason`` is non-None on the first
    malformed entry (missing causal id) or duplicate causal id.
    """
    mapping: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            return {}, "malformed_journal_entry"
        causal_id = entry.get(id_key)
        if not isinstance(causal_id, str):
            return {}, "missing_causal_id"
        if causal_id in mapping:
            # One effect must journal exactly one entry of each kind.
            return {}, "duplicate_causal_id"
        mapping[causal_id] = entry
    return mapping, None


def verify_intent_result_bijection(
    intents: list[Any],
    results: list[Any],
) -> BijectionResult:
    """Verify an exact one-to-one intent/result correspondence (D-5).

    Requires: no duplicate causal ids on either side; the same set of
    causal ids on both sides (no orphan intent, no orphan result); and,
    per causal id, the intent and result agree on the syscall name.
    Fail-closed: the first deviation returns a failure with an opaque
    reason and the offending causal id when applicable.
    """
    intent_map, reason = _index_by_causal_id(intents, id_key="causal_id")
    if reason is not None:
        return BijectionResult.failure(f"intent_{reason}")
    result_map, reason = _index_by_causal_id(results, id_key="syscall_id")
    if reason is not None:
        return BijectionResult.failure(f"result_{reason}")

    intent_ids = set(intent_map)
    result_ids = set(result_map)

    orphan_intents = intent_ids - result_ids
    if orphan_intents:
        # An engaged effect with no journaled result: the effect may
        # have run without recording its outcome.
        return BijectionResult.failure(
            "intent_without_result", detail=sorted(orphan_intents)[0]
        )
    orphan_results = result_ids - intent_ids
    if orphan_results:
        # A journaled effect with no pre-effect engagement: an effect
        # ran that was never engaged.
        return BijectionResult.failure(
            "result_without_intent", detail=sorted(orphan_results)[0]
        )

    for causal_id in intent_ids:
        intent_syscall = intent_map[causal_id].get("syscall")
        result_syscall = result_map[causal_id].get("syscall")
        if intent_syscall != result_syscall:
            return BijectionResult.failure("syscall_mismatch", detail=causal_id)
        # Campaign 6 (Lot 2, closes a8 section 9): this exact result
        # closes this exact intent. An intent without an engagement
        # digest proves nothing; a result without the equal digest may
        # close a different intent of the same syscall (permutation).
        intent_commitment = intent_map[causal_id].get("commitment_sha256")
        if not isinstance(intent_commitment, str) or not intent_commitment:
            return BijectionResult.failure(
                "intent_missing_commitment", detail=causal_id
            )
        result_commitment = result_map[causal_id].get("intent_commitment_sha256")
        if result_commitment != intent_commitment:
            return BijectionResult.failure(
                "intent_commitment_mismatch", detail=causal_id
            )

    return BijectionResult.success()


__all__ = ["BijectionResult", "verify_intent_result_bijection"]
