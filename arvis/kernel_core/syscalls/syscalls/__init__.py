# # arvis/kernel_core/syscalls/syscalls/__init__.py

from __future__ import annotations

from . import (
    interrupt_syscalls,
    llm_syscalls,
    memory_syscalls,
    process_syscalls,
    tool_syscalls,
    vfs_syscalls,
)

__all__ = [
    "interrupt_syscalls",
    "llm_syscalls",
    "memory_syscalls",
    "process_syscalls",
    "tool_syscalls",
    "vfs_syscalls",
]
