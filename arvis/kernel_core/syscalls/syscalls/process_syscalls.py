# arvis/kernel_core/syscalls/syscalls/process_syscalls.py

from __future__ import annotations

from typing import Any, Protocol

from arvis.errors.base import (
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.kernel_core.process import CognitiveProcessId
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall


class SchedulerLike(Protocol):
    def enqueue(self, process: Any) -> None: ...
    def suspend(self, process_id: CognitiveProcessId) -> None: ...
    def resume(self, process_id: CognitiveProcessId) -> None: ...


class SyscallHandlerLike(Protocol):
    scheduler: SchedulerLike


@register_syscall("process.spawn")
def process_spawn(
    handler: SyscallHandlerLike,
    process: Any,
) -> SyscallResult:
    try:
        handler.scheduler.enqueue(process)
    except Exception as exc:
        return SyscallResult.failure(
            ArvisRuntimeError(
                str(exc),
                code="process_spawn_failed",
                domain=ErrorDomain.KERNEL,
                details={
                    "exception": type(exc).__name__,
                    "retry_class": "transient",
                },
                replay_safe=False,
            )
        )
    return SyscallResult(success=True)


@register_syscall("process.suspend")
def process_suspend(
    handler: SyscallHandlerLike,
    process_id: CognitiveProcessId,
) -> SyscallResult:
    try:
        handler.scheduler.suspend(process_id)
    except Exception as exc:
        return SyscallResult.failure(
            ArvisRuntimeError(
                str(exc),
                code="process_suspend_failed",
                domain=ErrorDomain.KERNEL,
                details={
                    "exception": type(exc).__name__,
                    "retry_class": "transient",
                },
                replay_safe=False,
            )
        )

    return SyscallResult(success=True)


@register_syscall("process.resume")
def process_resume(
    handler: SyscallHandlerLike,
    process_id: CognitiveProcessId,
) -> SyscallResult:
    try:
        handler.scheduler.resume(process_id)
    except Exception as exc:
        return SyscallResult.failure(
            ArvisRuntimeError(
                str(exc),
                code="process_resume_failed",
                domain=ErrorDomain.KERNEL,
                details={
                    "exception": type(exc).__name__,
                    "retry_class": "transient",
                },
                replay_safe=False,
            )
        )

    return SyscallResult(success=True)
