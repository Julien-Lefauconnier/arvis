# # arvis/kernel_core/syscalls/syscalls/__init__.py

from __future__ import annotations

from . import interrupt_syscalls
from . import memory_syscalls
from . import process_syscalls
from . import tool_syscalls
from . import vfs_syscalls

__all__ = [
    "interrupt_syscalls",
    "memory_syscalls",
    "process_syscalls",
    "tool_syscalls",
    "vfs_syscalls",
]
