# arvis/kernel_core/syscalls/syscalls/interrupt_syscalls.py

from __future__ import annotations

from typing import Protocol, Any

from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall


class InterruptBusLike(Protocol):
    def emit(self, interrupt: Any) -> None: ...


class RuntimeStateLike(Protocol):
    interrupt_bus: InterruptBusLike


class SyscallHandlerLike(Protocol):
    runtime_state: RuntimeStateLike | None

@register_syscall("interrupt.emit")
def interrupt_emit(
    handler: SyscallHandlerLike,
    interrupt: Any,
) -> SyscallResult:
    if handler.runtime_state is None:
        return SyscallResult(
            success=False,
            error="no_runtime_state",
        )

    handler.runtime_state.interrupt_bus.emit(interrupt)

    return SyscallResult(success=True)