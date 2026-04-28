# arvis/kernel_core/syscalls/syscalls/process_syscalls.py

from __future__ import annotations

from typing import Protocol, Any

from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall

from arvis.kernel_core.process import CognitiveProcessId


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
    handler.scheduler.enqueue(process)
    return SyscallResult(success=True)


@register_syscall("process.suspend")
def process_suspend(
    handler: SyscallHandlerLike,
    process_id: CognitiveProcessId,
) -> SyscallResult:
    handler.scheduler.suspend(process_id)
    return SyscallResult(success=True)


@register_syscall("process.resume")
def process_resume(
    handler: SyscallHandlerLike,
    process_id: CognitiveProcessId,
) -> SyscallResult:
    handler.scheduler.resume(process_id)
    return SyscallResult(success=True)
