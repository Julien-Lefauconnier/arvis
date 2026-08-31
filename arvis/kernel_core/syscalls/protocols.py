# arvis/kernel_core/syscalls/protocols.py
"""Canonical structural views consumed by the syscall layer.

One definition per concept (campaign STRUCT, LOT S2). The syscall
layer used to re-declare these shapes locally in every module (seven
SyscallHandlerLike, four PipelineContextLike, three RuntimeStateLike),
each describing a different slice of the same runtime objects, several
degraded to ``Any``. The layer now types its plumbing against the real
``SyscallHandler`` where it can (same package), and against the
protocols below for the objects the kernel core must not import at
runtime (the runtime state and the pipeline context live in upper
layers).

Attribute members that the layer only reads are declared as read-only
properties: a plain protocol attribute is invariant under mypy, which
would reject the concrete runtime classes whose fields carry the
concrete types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from arvis.kernel_core.interrupts.interrupt import CognitiveInterrupt
    from arvis.kernel_core.process import CognitiveProcess, CognitiveProcessId


class SchedulerStateLike(Protocol):
    """The scheduler-state slice the syscall layer reads."""

    tick_count: int


class InterruptBusLike(Protocol):
    """The interrupt bus surface the syscall layer drives."""

    def emit(self, interrupt: CognitiveInterrupt) -> None: ...


class SchedulerLike(Protocol):
    """The scheduler surface process syscalls drive."""

    def enqueue(self, process: CognitiveProcess) -> None: ...

    def suspend(self, process_id: CognitiveProcessId) -> None: ...

    def resume(self, process_id: CognitiveProcessId) -> None: ...


class RuntimeStateLike(Protocol):
    """The runtime-state surface the syscall layer consumes.

    The concrete object is the runtime's ``CognitiveRuntimeState``
    (an upper layer the kernel core must not import at runtime); this
    protocol is the union of what the handler, the outbox and the
    interrupt syscalls actually use.
    """

    @property
    def scheduler_state(self) -> SchedulerStateLike: ...

    @property
    def interrupt_bus(self) -> InterruptBusLike: ...

    def append_event(self, name: str, payload: dict[str, Any]) -> None: ...


class PipelineContextLike(Protocol):
    """The pipeline-context slice the syscall layer journals into.

    The concrete object is the kernel pipeline context (upper layer);
    the syscall layer only ever touches its ``extra`` channel and,
    defensively, attributes it reads through ``getattr``.
    """

    extra: dict[str, Any]
