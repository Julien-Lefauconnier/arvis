# tests/api/test_audit_journal_absence.py
"""Campaign KERNEL (LOT K2), RED-first: an ABSENT audit journal is not
an EMPTY one.

The commitment gatherer read the two journals with
``getattr(state, "syscall_intents", None) or []``, so a renamed or
missing attribute became an empty list, and an empty/empty pair
satisfies the strict D-5 bijection vacuously. A run whose journal
could not be read was therefore committed as if the audit had proved
something. That is the same shape as the two structurally dead layers
found earlier in this repo: a getattr that answers None forever.

An empty journal remains perfectly legitimate: most turns invoke no
effect syscall at all. The distinction is present-and-empty (nothing
happened) versus absent (nothing can be asserted).
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.api.os import CognitiveOS


def _os() -> CognitiveOS:
    return CognitiveOS()


def _result(execution_state: object) -> object:
    return SimpleNamespace(execution=SimpleNamespace(execution_state=execution_state))


def test_a_present_but_empty_journal_stays_committable() -> None:
    """The common case: no effect syscall ran this turn."""
    state = SimpleNamespace(
        syscall_intents=[],
        syscall_results=[],
        metadata={},
    )

    inputs, reason = _os()._build_commitment_inputs(_result(state))

    assert reason is None
    assert inputs is not None


def test_a_missing_journal_attribute_is_audit_incomplete() -> None:
    """A renamed or absent journal must refuse the commitment rather
    than pass the bijection vacuously."""
    state = SimpleNamespace(metadata={})  # neither journal present

    inputs, reason = _os()._build_commitment_inputs(_result(state))

    assert reason == "audit_incomplete"
    assert inputs is None


def test_a_non_list_journal_is_audit_incomplete() -> None:
    state = SimpleNamespace(
        syscall_intents=None,
        syscall_results=[],
        metadata={},
    )

    inputs, reason = _os()._build_commitment_inputs(_result(state))

    assert reason == "audit_incomplete"
    assert inputs is None
