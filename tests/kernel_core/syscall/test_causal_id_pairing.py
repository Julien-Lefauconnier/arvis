# tests/kernel_core/syscall/test_causal_id_pairing.py
"""Campaign KERNEL (LOT K2), RED-first: the journaled result must
carry the causal id the intent was minted with.

``handle()`` computes the causal id from the handler's local
sequence counter, then ``_journal`` REBUILT another one from the same
counter. The counter advances once per ``handle()``, so any nested
dispatch shifts it between the two reads: the outer result is
journaled under the inner's sequence number, its intent is orphaned,
and the strict D-5 bijection reports a perfectly legitimate run as
unauditable. The outer result also loses its intent commitment, and
the pending entry leaks for the life of the run.
"""

from __future__ import annotations

from typing import Any

from arvis.kernel_core.syscalls.intent_result_bijection import (
    verify_intent_result_bijection,
)
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SYSCALL_REGISTRY,
    SyscallEffect,
    register_syscall,
)


class _Ctx:
    """Minimal host context: the journal lives on ctx.extra."""

    def __init__(self) -> None:
        self.extra: dict[str, Any] = {}


captured: dict[str, Any] = {}


def _register_nested_probe(handler: SyscallHandler) -> None:
    @register_syscall("probe.inner", effect=SyscallEffect.READ, summary="nested probe")
    def _inner(handler: SyscallHandler, **kwargs: Any) -> SyscallResult:
        return SyscallResult.ok({"ok": True})

    @register_syscall("probe.outer", effect=SyscallEffect.READ, summary="outer probe")
    def _outer(
        inner_handler: SyscallHandler,
        *,
        ctx: Any = None,
        causal_id: str | None = None,
        **kwargs: Any,
    ) -> SyscallResult:
        # A syscall whose body dispatches another one through the same
        # handler: the documented composition, and what shifts the
        # sequence counter under the outer call. The body is handed the
        # causal id its intent was minted with, which is exactly the id
        # its journaled result must carry.
        captured["outer_causal_id"] = causal_id
        inner_handler.handle(Syscall(name="probe.inner", args={"ctx": ctx}))
        return SyscallResult.ok({"ok": True})


def _cleanup_probes() -> None:
    for name in ("probe.inner", "probe.outer"):
        SYSCALL_REGISTRY.pop(name, None)
        SYSCALL_DESCRIPTORS.pop(name, None)


def test_a_nested_dispatch_keeps_the_result_paired_with_its_intent() -> None:
    handler = SyscallHandler(runtime_state=None, scheduler=None)
    _register_nested_probe(handler)
    ctx = _Ctx()

    try:
        handler.handle(Syscall(name="probe.outer", args={"ctx": ctx}))
    finally:
        _cleanup_probes()

    results = ctx.extra.get("syscall_results", [])
    ids = [entry.get("syscall_id") for entry in results]

    assert len(ids) == 2, results
    # each journaled result must carry its OWN causal id; the outer one
    # must not be re-stamped with the inner's sequence number
    assert len(set(ids)) == 2, ids
    outer = next(e for e in results if e.get("syscall") == "probe.outer")
    inner = next(e for e in results if e.get("syscall") == "probe.inner")
    assert outer["syscall_id"] != inner["syscall_id"]
    # and it must be the very id the intent was minted with
    assert outer["syscall_id"] == captured["outer_causal_id"]


def test_nesting_does_not_break_the_bijection() -> None:
    """The user-visible consequence: a legitimate nested run must stay
    auditable instead of being reported audit-incomplete."""
    handler = SyscallHandler(runtime_state=None, scheduler=None)
    _register_nested_probe(handler)
    ctx = _Ctx()

    try:
        handler.handle(Syscall(name="probe.outer", args={"ctx": ctx}))
    finally:
        _cleanup_probes()

    intents = ctx.extra.get("syscall_intents", [])
    results = ctx.extra.get("syscall_results", [])
    if not intents:
        # non-effect syscalls journal no intent: the bijection is then
        # vacuous by construction and this assertion does not apply
        return

    assert verify_intent_result_bijection(intents, results).ok
