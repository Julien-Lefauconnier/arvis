# tests/kernel_core/test_interrupt_bus_surface.py
"""The interrupt bus is exactly what the runtime drives.

Campaign HARDEN (DM-H4 option A, audit P1-15b, 2026-09-02). The bus
carried a subscribe/unsubscribe half and a per-type subscriber table
with zero callers anywhere in arvis or its tests: dead API that
documented a pub/sub the runtime does not have. The dead half is
removed; these pins keep the surface honest (explicit-target routing
only) so it cannot quietly grow back without a design act.
"""

from __future__ import annotations

from arvis.kernel_core.interrupts.interrupt import CognitiveInterrupt
from arvis.kernel_core.interrupts.interrupt_bus import CognitiveInterruptBus
from arvis.kernel_core.interrupts.interrupt_type import CognitiveInterruptType
from arvis.kernel_core.process.process_interrupt_state import (
    ProcessInterruptState,
)


def _interrupt(target: str | None) -> CognitiveInterrupt:
    return CognitiveInterrupt(
        type=CognitiveInterruptType.USER_INPUT,
        target_process_id=target,
    )


def test_the_dead_pub_sub_half_stays_removed() -> None:
    bus = CognitiveInterruptBus()
    assert not hasattr(bus, "subscribe")
    assert not hasattr(bus, "unsubscribe")
    assert not hasattr(bus, "_subscribers")
    assert not hasattr(ProcessInterruptState(), "subscribed_interrupts")


def test_match_routes_by_explicit_target_only() -> None:
    bus = CognitiveInterruptBus()
    assert bus.match(_interrupt("p1")) == ["p1"]
    assert bus.match(_interrupt(None)) == []


def test_emit_then_drain_hands_over_the_batch_once() -> None:
    bus = CognitiveInterruptBus()
    first = _interrupt("p1")
    second = _interrupt(None)
    bus.emit(first)
    bus.emit(second)
    assert bus.drain() == [first, second]
    assert bus.drain() == []
