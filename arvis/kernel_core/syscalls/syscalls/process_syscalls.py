# arvis/kernel_core/syscalls/syscalls/process_syscalls.py

from __future__ import annotations

from typing import Any, Protocol

from arvis.errors.base import (
    ErrorDomain,
)
from arvis.errors.manager import ErrorManager
from arvis.errors.provenance import ErrorOrigin
from arvis.kernel_core.access.resolvers import kernel_internal_resolver
from arvis.kernel_core.process import CognitiveProcessId
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    register_syscall,
)


class SchedulerLike(Protocol):
    def enqueue(self, process: Any) -> None: ...
    def suspend(self, process_id: CognitiveProcessId) -> None: ...
    def resume(self, process_id: CognitiveProcessId) -> None: ...


class SyscallHandlerLike(Protocol):
    scheduler: SchedulerLike


@register_syscall(
    "process.spawn",
    effect=SyscallEffect.EFFECT,
    summary="Spawn a new cognitive process.",
    access=kernel_internal_resolver("process.spawn"),
)
def process_spawn(
    handler: SyscallHandlerLike,
    process: Any,
) -> SyscallResult:
    try:
        handler.scheduler.enqueue(process)
    except Exception as exc:
        return SyscallResult.failure(
            ErrorManager.normalize_for_boundary(
                exc,
                boundary="runtime",
                code="process_spawn_failed",
                domain=ErrorDomain.KERNEL,
                origin=ErrorOrigin(
                    component="process.spawn", subsystem="kernel.syscall"
                ),
                details={
                    "retry_class": "transient",
                },
                replay_safe=False,
            )
        )
    return SyscallResult(success=True)


@register_syscall(
    "process.suspend",
    effect=SyscallEffect.EFFECT,
    summary="Suspend a running cognitive process.",
    access=kernel_internal_resolver("process.suspend"),
)
def process_suspend(
    handler: SyscallHandlerLike,
    process_id: CognitiveProcessId,
) -> SyscallResult:
    try:
        handler.scheduler.suspend(process_id)
    except Exception as exc:
        return SyscallResult.failure(
            ErrorManager.normalize_for_boundary(
                exc,
                boundary="runtime",
                code="process_suspend_failed",
                domain=ErrorDomain.KERNEL,
                origin=ErrorOrigin(
                    component="process.suspend", subsystem="kernel.syscall"
                ),
                details={
                    "retry_class": "transient",
                },
                replay_safe=False,
            )
        )

    return SyscallResult(success=True)


@register_syscall(
    "process.resume",
    effect=SyscallEffect.EFFECT,
    summary="Resume a suspended cognitive process.",
    access=kernel_internal_resolver("process.resume"),
)
def process_resume(
    handler: SyscallHandlerLike,
    process_id: CognitiveProcessId,
) -> SyscallResult:
    try:
        handler.scheduler.resume(process_id)
    except Exception as exc:
        return SyscallResult.failure(
            ErrorManager.normalize_for_boundary(
                exc,
                boundary="runtime",
                code="process_resume_failed",
                domain=ErrorDomain.KERNEL,
                origin=ErrorOrigin(
                    component="process.resume", subsystem="kernel.syscall"
                ),
                details={
                    "retry_class": "transient",
                },
                replay_safe=False,
            )
        )

    return SyscallResult(success=True)
