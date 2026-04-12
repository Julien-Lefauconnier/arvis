# # arvis/kernel_core/syscalls/syscalls/__init__.py

from __future__ import annotations

# Import built-in syscall modules so decorators execute at package import time.
from arvis.kernel_core.syscalls.syscalls import tool_syscalls

__all__ = [
    "tool_syscalls",
]