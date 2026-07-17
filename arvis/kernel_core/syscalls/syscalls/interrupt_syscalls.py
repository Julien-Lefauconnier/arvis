# arvis/kernel_core/syscalls/syscalls/interrupt_syscalls.py

from __future__ import annotations

from typing import Any, Protocol

from arvis.errors.base import (
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.kernel_core.access.resolvers import kernel_internal_resolver
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    register_syscall,
)


class InterruptBusLike(Protocol):
    def emit(self, interrupt: Any) -> None: ...


class RuntimeStateLike(Protocol):
    interrupt_bus: InterruptBusLike


class SyscallHandlerLike(Protocol):
    runtime_state: RuntimeStateLike | None


@register_syscall(
    "interrupt.emit",
    effect=SyscallEffect.EFFECT,
    summary="Emit a runtime interrupt signal.",
    access=kernel_internal_resolver("interrupt.emit"),
)
def interrupt_emit(
    handler: SyscallHandlerLike,
    interrupt: Any,
    *,
    ctx: Any = None,
    causal_id: str | None = None,
) -> SyscallResult:
    if handler.runtime_state is None:
        return SyscallResult.failure(
            ArvisRuntimeError(
                "Runtime state not configured",
                code="no_runtime_state",
                domain=ErrorDomain.KERNEL,
            )
        )

    handler.runtime_state.interrupt_bus.emit(interrupt)

    return SyscallResult(success=True)
