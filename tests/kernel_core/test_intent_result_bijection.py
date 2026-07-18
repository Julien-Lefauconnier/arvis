# tests/kernel_core/test_intent_result_bijection.py
"""Strict intent/result bijection (campaign 5, Lot 4, closes P1-6).

The a7 membership check ("each intent's causal id appears among the
result ids") missed duplicate intents, orphan results and syscall
mismatches. Each of those a7 gaps is pinned here as a refusal, plus the
exact one-to-one success case and the empty (no-effect) case.
"""

from __future__ import annotations

from arvis.kernel_core.syscalls.intent_result_bijection import (
    BijectionResult,
    verify_intent_result_bijection,
)


def _intent(causal_id: str, syscall: str = "tool.execute") -> dict:
    return {"causal_id": causal_id, "syscall": syscall}


def _result(causal_id: str, syscall: str = "tool.execute") -> dict:
    return {"syscall_id": causal_id, "syscall": syscall}


# ---------------------------------------------------------------
# Success and the trivial case
# ---------------------------------------------------------------


def test_exact_one_to_one_is_ok():
    result = verify_intent_result_bijection(
        [_intent("c1"), _intent("c2", "mail.send")],
        [_result("c1"), _result("c2", "mail.send")],
    )
    assert result.ok is True
    assert result.reason is None


def test_empty_journals_are_ok():
    # No effect: an empty bijection is valid (nothing to prove).
    assert verify_intent_result_bijection([], []).ok is True


# ---------------------------------------------------------------
# The a7 gaps, now refused
# ---------------------------------------------------------------


def test_duplicate_intent_is_refused():
    result = verify_intent_result_bijection(
        [_intent("c1"), _intent("c1")],
        [_result("c1")],
    )
    assert result.ok is False
    assert result.reason == "intent_duplicate_causal_id"


def test_duplicate_result_is_refused():
    result = verify_intent_result_bijection(
        [_intent("c1")],
        [_result("c1"), _result("c1")],
    )
    assert result.ok is False
    assert result.reason == "result_duplicate_causal_id"


def test_orphan_result_is_refused():
    # An effect that ran with no pre-effect engagement.
    result = verify_intent_result_bijection(
        [_intent("c1")],
        [_result("c1"), _result("c2")],
    )
    assert result.ok is False
    assert result.reason == "result_without_intent"
    assert result.detail == "c2"


def test_orphan_intent_is_refused():
    # An engaged effect with no journaled result.
    result = verify_intent_result_bijection(
        [_intent("c1"), _intent("c2")],
        [_result("c1")],
    )
    assert result.ok is False
    assert result.reason == "intent_without_result"
    assert result.detail == "c2"


def test_syscall_mismatch_is_refused():
    result = verify_intent_result_bijection(
        [_intent("c1", "mail.send")],
        [_result("c1", "vfs.write")],
    )
    assert result.ok is False
    assert result.reason == "syscall_mismatch"
    assert result.detail == "c1"


# ---------------------------------------------------------------
# Malformed journals fail closed
# ---------------------------------------------------------------


def test_missing_causal_id_on_intent_is_refused():
    result = verify_intent_result_bijection(
        [{"syscall": "tool.execute"}],
        [_result("c1")],
    )
    assert result.ok is False
    assert result.reason == "intent_missing_causal_id"


def test_missing_id_on_result_is_refused():
    result = verify_intent_result_bijection(
        [_intent("c1")],
        [{"syscall": "tool.execute"}],
    )
    assert result.ok is False
    assert result.reason == "result_missing_causal_id"


def test_malformed_entry_is_refused():
    result = verify_intent_result_bijection(["not-a-dict"], [])
    assert result.ok is False
    assert result.reason == "intent_malformed_journal_entry"


# ---------------------------------------------------------------
# Result value type
# ---------------------------------------------------------------


def test_bijection_result_helpers():
    assert BijectionResult.success().ok is True
    fail = BijectionResult.failure("some_reason", detail="c9")
    assert fail.ok is False
    assert fail.reason == "some_reason"
    assert fail.detail == "c9"
